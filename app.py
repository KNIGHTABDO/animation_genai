import streamlit as st
import google.generativeai as genai
import subprocess
import os
import tempfile
import shutil
from pathlib import Path
import time
import uuid
from dotenv import load_dotenv
import re

# Configure the page
st.set_page_config(
    page_title="Manim Animation Generator",
    page_icon="🎬",
    layout="wide"
)

# Title and description
st.title("🎬 Manim Animation Generator")
st.markdown("Generate 2D educational animations in the style of 3Blue1Brown using AI with self-correction")

# Load API key from .env file
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=api_key)

# Default model - will be overridden by user selection
DEFAULT_MODEL = 'gemini-2.0-flash-exp'
model = None  # Will be initialized based on user selection

def get_enhanced_system_prompt():
    """Enhanced system prompt with comprehensive Manim guidelines"""
    return """You are an expert Manim developer specializing in creating educational animations like 3Blue1Brown. You MUST generate syntactically correct Manim Community Edition v0.19.0 code.

🎯 CRITICAL SUCCESS CRITERIA:
1. Generate WORKING, ERROR-FREE Manim code that renders successfully
2. Use ONLY modern Manim Community v0.19.0+ syntax
3. Create engaging, educational content with smooth animations
4. Follow 3Blue1Brown's pedagogical style and visual aesthetics

📋 MANDATORY SYNTAX REQUIREMENTS (v0.19.0+):

🔸 SCENE STRUCTURE:
- Class MUST be named 'MainScene' inheriting from Scene
- Use construct(self) method for all animation logic
- Start with: from manim import *

🔸 TEXT AND MATH:
✅ CORRECT: Text("Hello World")
✅ CORRECT: MathTex(r"x^2 + y^2 = z^2")
❌ WRONG: TextMobject, TexMobject (DEPRECATED)

🔸 POSITIONING:
✅ CORRECT: obj.move_to(ORIGIN), obj.center(), obj.shift(UP)
❌ WRONG: obj.to_center() (DEPRECATED)

🔸 AXES CONFIGURATION (CRITICAL):
✅ CORRECT: 
```python
axes = Axes(
    x_range=[-3, 3, 1],  # [min, max, step]
    y_range=[-2, 2, 1],
    x_length=6,
    y_length=4,
    axis_config={"color": BLUE}  # Visual properties only
)
```
❌ WRONG: Putting x_range/y_range inside x_axis_config or y_axis_config

🔸 GRAPH PLOTTING:
✅ CORRECT: 
```python
func = lambda x: x**2  # Define function first
graph = axes.plot(func, x_range=[-2, 2], color=BLUE)
```
❌ WRONG: axes.get_graph() (DEPRECATED)

🔸 ANIMATIONS:
- Use self.play() for animations
- Use self.add() for instant additions
- Use self.wait(duration) for pauses
- Common animations: Write, Create, Transform, FadeIn, FadeOut, DrawBorderThenFill

🔸 COLORS:
Use Manim constants: BLUE, RED, GREEN, YELLOW, PURPLE, ORANGE, WHITE, BLACK

🎨 EDUCATIONAL DESIGN PRINCIPLES:
1. Start with a clear title and introduction
2. Build concepts step by step
3. Use visual metaphors and analogies
4. Highlight key insights with color changes
5. Include mathematical expressions when relevant
6. End with a summary or key takeaway
7. Use smooth transitions between concepts

🔧 CODE STRUCTURE TEMPLATE:
```python
from manim import *

class MainScene(Scene):
    def construct(self):
        # 1. Title and introduction
        title = Text("Your Educational Topic", font_size=48)
        title.move_to(ORIGIN + UP * 2)
        self.play(Write(title))
        self.wait()
        
        # 2. Main content with step-by-step building
        # Your educational content here
        
        # 3. Mathematical expressions (if needed)
        equation = MathTex(r"f(x) = x^2")
        equation.move_to(ORIGIN)
        self.play(Write(equation))
        
        # 4. Visual elements (graphs, shapes, etc.)
        if using_axes:
            axes = Axes(
                x_range=[-3, 3, 1],
                y_range=[-2, 2, 1]
            )
            func = lambda x: x**2
            graph = axes.plot(func, x_range=[-2, 2])
            self.play(Create(axes), Create(graph))
        
        # 5. Animations and transformations
        self.play(Transform(old_obj, new_obj))
        self.wait()
        
        # 6. Conclusion
        conclusion = Text("Key Insight: [Your insight here]")
        self.play(Write(conclusion))
        self.wait(2)
```

⚠️ CRITICAL REQUIREMENTS:
- Return ONLY Python code, no markdown formatting
- Do NOT wrap in ```python``` blocks
- Ensure all objects are properly positioned
- Test all syntax mentally before generating
- Use descriptive variable names
- Include appropriate wait() statements for pacing
- Make animations educational and engaging

Remember: The goal is to create animations that help viewers understand complex concepts through visual storytelling, just like 3Blue1Brown does."""

def get_error_analysis_prompt(error_message, script_content):
    """Generate a prompt for analyzing and fixing errors"""
    return f"""You are debugging a Manim script that failed to render. Analyze the error and generate a corrected version.

ERROR MESSAGE:
{error_message}

ORIGINAL SCRIPT:
{script_content}

🔍 DEBUGGING INSTRUCTIONS:
1. Carefully analyze the error message to identify the root cause
2. Check for common Manim syntax issues:
   - Deprecated methods (to_center, TexMobject, TextMobject, get_graph)
   - Incorrect axes configuration (x_range/y_range in wrong place)
   - Missing imports or undefined variables
   - Incorrect parameter names or values
   - Animation syntax errors

3. Apply the correct Manim Community v0.19.0+ syntax
4. Ensure all objects are properly defined before use
5. Verify all function calls use correct parameters

CRITICAL: Generate a COMPLETE, corrected script that will render successfully. 
Return ONLY the corrected Python code with no markdown formatting.
The script must start with 'from manim import *' and contain a MainScene class."""

def generate_manim_script(prompt, attempt=1, previous_error=None, previous_script=None, selected_model=None):
    """Generate a Manim script using Gemini API with self-correction"""
    try:
        # Initialize model if not already done or if model changed
        if selected_model:
            current_model = genai.GenerativeModel(selected_model)
        else:
            current_model = genai.GenerativeModel(DEFAULT_MODEL)
        
        if attempt == 1:
            # First attempt - use enhanced system prompt
            system_prompt = get_enhanced_system_prompt()
            full_prompt = f"{system_prompt}\n\nCreate an educational animation about: {prompt}"
        else:
            # Subsequent attempts - use error analysis prompt
            system_prompt = get_error_analysis_prompt(previous_error, previous_script)
            full_prompt = f"{system_prompt}\n\nFix the errors and regenerate the script for: {prompt}"
        
        # Configure generation settings for better quality
        generation_config = {
            'temperature': 0.7,
            'top_p': 0.95,
            'top_k': 40,
            'max_output_tokens': 8192,
        }
        
        response = current_model.generate_content(
            full_prompt,
            generation_config=generation_config
        )
        script = response.text.strip()
        
        # Clean the response - remove markdown code blocks if present
        script = clean_script_response(script)
        
        return script
    except Exception as e:
        st.error(f"Error generating script (attempt {attempt}): {str(e)}")
        return None

def clean_script_response(script):
    """Clean the AI response to extract pure Python code"""
    # Remove markdown code blocks
    if script.startswith('```python'):
        script = script[9:]
    elif script.startswith('```'):
        script = script[3:]
    
    if script.endswith('```'):
        script = script[:-3]
    
    # Remove any leading/trailing whitespace
    script = script.strip()
    
    # Ensure it starts with the import statement
    if not script.startswith('from manim import'):
        # Find the import line and move it to the beginning
        lines = script.split('\n')
        import_line = None
        other_lines = []
        
        for line in lines:
            if line.strip().startswith('from manim import'):
                import_line = line
            else:
                other_lines.append(line)
        
        if import_line:
            script = import_line + '\n' + '\n'.join(other_lines)
    
    return script

def analyze_error_message(stderr):
    """Analyze error message and extract relevant information"""
    error_info = {
        'type': 'Unknown',
        'details': stderr,
        'suggestions': []
    }
    
    # Common error patterns and suggestions
    error_patterns = [
        {
            'pattern': r'multiple values for argument [\'"]x_range[\'"]',
            'type': 'Axes Configuration Error',
            'suggestion': 'Move x_range and y_range out of axis_config and into main Axes parameters'
        },
        {
            'pattern': r'AttributeError.*to_center',
            'type': 'Deprecated Method',
            'suggestion': 'Replace .to_center() with .move_to(ORIGIN) or .center()'
        },
        {
            'pattern': r'NameError.*TexMobject',
            'type': 'Deprecated Class',
            'suggestion': 'Replace TexMobject with MathTex'
        },
        {
            'pattern': r'NameError.*TextMobject',
            'type': 'Deprecated Class',
            'suggestion': 'Replace TextMobject with Text'
        },
        {
            'pattern': r'AttributeError.*get_graph',
            'type': 'Deprecated Method',
            'suggestion': 'Replace axes.get_graph() with axes.plot()'
        },
        {
            'pattern': r'TypeError.*unexpected keyword argument',
            'type': 'Parameter Error',
            'suggestion': 'Check parameter names and remove invalid arguments'
        }
    ]
    
    for pattern_info in error_patterns:
        if re.search(pattern_info['pattern'], stderr, re.IGNORECASE):
            error_info['type'] = pattern_info['type']
            error_info['suggestions'].append(pattern_info['suggestion'])
    
    return error_info

def auto_fix_manim_syntax(script_content):
    """Automatically fix common Manim syntax issues"""
    fixes_applied = []
    
    # Fix .to_center() -> .move_to(ORIGIN)
    if '.to_center()' in script_content:
        script_content = script_content.replace('.to_center()', '.move_to(ORIGIN)')
        fixes_applied.append("Replaced .to_center() with .move_to(ORIGIN)")
    
    # Fix TexMobject -> MathTex
    if 'TexMobject' in script_content:
        script_content = script_content.replace('TexMobject', 'MathTex')
        fixes_applied.append("Replaced TexMobject with MathTex")
    
    # Fix TextMobject -> Text
    if 'TextMobject' in script_content:
        script_content = script_content.replace('TextMobject', 'Text')
        fixes_applied.append("Replaced TextMobject with Text")
    
    # Fix axes configuration
    script_content, axes_fixes = fix_axes_configurations(script_content)
    fixes_applied.extend(axes_fixes)
    
    # Fix get_graph syntax
    pattern = r'\.get_graph\((.*?)\)'
    if re.search(pattern, script_content):
        script_content = re.sub(pattern, r'.plot(\1)', script_content)
        fixes_applied.append("Replaced .get_graph() with .plot()")
    
    return script_content, fixes_applied

def fix_axes_configurations(script_content):
    """Fix Axes configurations by moving x_range/y_range out of axis configs"""
    fixes_applied = []
    
    # Pattern to find problematic Axes configurations
    axes_pattern = r'Axes\s*\((.*?)\)'
    matches = re.finditer(axes_pattern, script_content, re.DOTALL)
    
    for match in matches:
        original = match.group(0)
        axes_content = match.group(1)
        
        # Check if x_range or y_range are in axis configs
        if 'x_axis_config' in axes_content and 'x_range' in axes_content:
            # Extract and fix
            fixed_axes = fix_single_axes_config(original)
            if fixed_axes != original:
                script_content = script_content.replace(original, fixed_axes)
                fixes_applied.append("Fixed Axes configuration - moved ranges out of axis configs")
    
    return script_content, fixes_applied

def fix_single_axes_config(axes_string):
    """Fix a single Axes configuration"""
    # This is a simplified version - you might want to enhance this
    # for more complex cases
    
    # Basic fix: if we see x_axis_config with x_range, try to extract it
    if 'x_axis_config' in axes_string and 'x_range' in axes_string:
        # Simple replacement for common patterns
        axes_string = re.sub(
            r'x_axis_config\s*=\s*\{\s*["\']x_range["\']\s*:\s*(\[.*?\])\s*\}',
            r'x_range=\1',
            axes_string
        )
    
    if 'y_axis_config' in axes_string and 'y_range' in axes_string:
        axes_string = re.sub(
            r'y_axis_config\s*=\s*\{\s*["\']y_range["\']\s*:\s*(\[.*?\])\s*\}',
            r'y_range=\1',
            axes_string
        )
    
    return axes_string

def save_and_render_script(script_content, session_id, auto_fix=True, max_attempts=3, selected_model=None):
    """Save the script and render it with Manim, with self-correction"""
    
    current_script = script_content
    attempt = 1
    
    while attempt <= max_attempts:
        try:
            # Apply automatic fixes if enabled and it's the first attempt
            if auto_fix and attempt == 1:
                current_script, fixes_applied = auto_fix_manim_syntax(current_script)
                if fixes_applied:
                    st.info(f"🔧 **Auto-fixes Applied (Attempt {attempt})**: {', '.join(fixes_applied)}")
            
            # Create a unique directory for this session
            work_dir = Path(f"manim_work_{session_id}_{attempt}")
            work_dir.mkdir(exist_ok=True)
            
            # Save the script with UTF-8 encoding
            script_path = work_dir / "animation.py"
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(current_script)
            
            # Run Manim to render the animation
            script_abs_path = script_path.resolve()
            cmd = [
                "manim", 
                str(script_abs_path),
                "MainScene",
                "-ql",
                "--disable_caching",
                f"--media_dir={work_dir.resolve()}/media"
            ]
            
            # Execute Manim
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            env['PYTHONLEGACYWINDOWSFSENCODING'] = '0'
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                encoding='utf-8',
                errors='ignore',
                env=env
            )
            
            if result.returncode == 0:
                # Success! Find the generated video file
                media_dir = work_dir / "media" / "videos" / "animation" / "480p15"
                possible_paths = [
                    media_dir,
                    work_dir / "media" / "videos" / "480p15",
                    work_dir / "media" / "videos",
                    work_dir / "media"
                ]
                
                video_path = None
                for path in possible_paths:
                    if path.exists():
                        video_files = list(path.glob("*.mp4"))
                        if video_files:
                            video_path = str(video_files[0])
                            break
                
                if video_path:
                    if attempt > 1:
                        st.success(f"✅ **Animation rendered successfully after {attempt} attempts!**")
                    return video_path, current_script
                else:
                    st.error("Video file not found after rendering")
                    return None, current_script
            
            else:
                # Rendering failed - analyze error and try to fix
                error_info = analyze_error_message(result.stderr)
                
                st.warning(f"⚠️ **Attempt {attempt} failed**: {error_info['type']}")
                
                if attempt < max_attempts:
                    st.info(f"🔄 **Attempting self-correction** (Attempt {attempt + 1}/{max_attempts})...")
                    
                    # Use AI to fix the error
                    with st.spinner("AI is analyzing and fixing the error..."):
                        corrected_script = generate_manim_script(
                            prompt="", # We'll use the error analysis prompt
                            attempt=attempt + 1,
                            previous_error=result.stderr,
                            previous_script=current_script,
                            selected_model=selected_model
                        )
                    
                    if corrected_script:
                        current_script = corrected_script
                        st.info("🤖 **AI has generated a corrected version**")
                    else:
                        st.error("Failed to generate corrected script")
                        break
                else:
                    # Final attempt failed
                    st.error(f"❌ **All {max_attempts} attempts failed**")
                    st.error(f"**Final Error Type**: {error_info['type']}")
                    
                    # Show suggestions
                    if error_info['suggestions']:
                        st.error("**Suggestions for manual fixing:**")
                        for suggestion in error_info['suggestions']:
                            st.error(f"• {suggestion}")
                    
                    with st.expander("View Full Error Details"):
                        st.code(f"STDOUT:\n{result.stdout}", language="text")
                        st.code(f"STDERR:\n{result.stderr}", language="text")
                    
                    return None, current_script
        
        except Exception as e:
            st.error(f"Error in attempt {attempt}: {str(e)}")
            if attempt >= max_attempts:
                return None, current_script
        
        attempt += 1
    
    return None, current_script

def main():
    # Initialize session state
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    
    if 'generated_script' not in st.session_state:
        st.session_state.generated_script = None
    
    if 'video_path' not in st.session_state:
        st.session_state.video_path = None
    
    # Settings in sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # Model selection
        st.subheader("🤖 AI Model")
        model_options = {
            "Gemini 2.0 Flash (Experimental) - Fast & Efficient": "gemini-2.0-flash-exp",
            "Gemini 2.0 Pro (Experimental) - Most Capable": "gemini-2.0-pro-exp",
            "Gemini 1.5 Flash (Stable) - Reliable & Fast": "gemini-1.5-flash",
            "Gemini 1.5 Pro (Stable) - Balanced Performance": "gemini-1.5-pro"
        }
        selected_model_name = st.selectbox(
            "Select Gemini Model",
            options=list(model_options.keys()),
            index=0,
            help="Choose the AI model for generating animations. Flash models are faster, Pro models are more capable."
        )
        selected_model = model_options[selected_model_name]
        
        st.markdown("---")
        
        auto_fix_enabled = st.checkbox(
            "🔧 Auto-fix syntax errors", 
            value=True,
            help="Automatically fix common outdated Manim syntax"
        )
        
        max_attempts = st.slider(
            "🔄 Max correction attempts",
            min_value=1,
            max_value=5,
            value=3,
            help="Maximum number of AI self-correction attempts"
        )
        
        st.markdown("---")
        st.markdown("**Features:**")
        st.markdown("• Latest Gemini 2.0 API")
        st.markdown("• Model selection options")
        st.markdown("• Enhanced AI prompts")
        st.markdown("• Self-error correction")
        st.markdown("• Modern Manim syntax")
        st.markdown("• 3Blue1Brown style")
    
    # Main interface
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.header("📝 Input")
        prompt = st.text_area(
            "Describe the educational concept you want to animate:",
            placeholder="e.g., Explain the Pythagorean theorem with a visual proof, demonstrate calculus derivatives, show how Fourier transforms work",
            height=100
        )
        
        generate_button = st.button("🎬 Generate Animation", type="primary")
        
        if generate_button and prompt and api_key:
            with st.spinner(f"🤖 Generating enhanced Manim script using {selected_model_name}..."):
                script = generate_manim_script(prompt, selected_model=selected_model)
            
            if script:
                st.session_state.generated_script = script
                st.session_state.session_id = str(uuid.uuid4())
                
                with st.spinner("🎬 Rendering animation with self-correction..."):
                    video_path, final_script = save_and_render_script(
                        script, 
                        st.session_state.session_id, 
                        auto_fix_enabled,
                        max_attempts,
                        selected_model
                    )
                    st.session_state.video_path = video_path
                    st.session_state.generated_script = final_script
                
                if video_path:
                    st.success("🎉 Animation generated successfully!")
                else:
                    st.error("❌ Failed to render animation after all attempts.")
        
        elif generate_button and not api_key:
            st.error("⚠️ Please set your GOOGLE_API_KEY in the .env file")
        elif generate_button and not prompt:
            st.error("⚠️ Please enter a prompt")
    
    with col2:
        st.header("🎥 Output")
        
        if st.session_state.video_path and os.path.exists(st.session_state.video_path):
            # Display the video
            with open(st.session_state.video_path, 'rb') as video_file:
                video_bytes = video_file.read()
                st.video(video_bytes)
            
            # Download button
            st.download_button(
                label="📥 Download Animation",
                data=video_bytes,
                file_name=f"manim_animation_{int(time.time())}.mp4",
                mime="video/mp4"
            )
        else:
            st.info("🎬 Generated animation will appear here")
    
    # Show generated script
    if st.session_state.generated_script:
        st.header("🐍 Generated Manim Script")
        with st.expander("View/Edit Script", expanded=False):
            edited_script = st.text_area(
                "Manim Python Script:",
                value=st.session_state.generated_script,
                height=300,
                help="You can edit the script and re-render it"
            )
            
            col_a, col_b = st.columns(2)
            with col_a:
                rerender_button = st.button("🔄 Re-render Script")
            with col_b:
                rerender_auto_fix = st.checkbox("🔧 Apply auto-fixes", value=True)
            
            if rerender_button:
                with st.spinner("🎬 Re-rendering with corrections..."):
                    st.session_state.session_id = str(uuid.uuid4())
                    video_path, final_script = save_and_render_script(
                        edited_script, 
                        st.session_state.session_id, 
                        rerender_auto_fix,
                        max_attempts,
                        selected_model
                    )
                    st.session_state.video_path = video_path
                    st.session_state.generated_script = final_script
                
                if video_path:
                    st.success("🎉 Animation re-rendered successfully!")
                    st.rerun()

if __name__ == "__main__":
    main()