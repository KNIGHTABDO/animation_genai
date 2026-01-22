import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load API key
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    print("❌ Error: GOOGLE_API_KEY not found in .env file")
    exit(1)

genai.configure(api_key=api_key)

print("🔍 Available Gemini Models:\n")
print("=" * 80)

models = genai.list_models()
for model in models:
    # Only show generative models
    if 'generateContent' in model.supported_generation_methods:
        print(f"\n📦 Model: {model.name}")
        print(f"   Display Name: {model.display_name}")
        print(f"   Description: {model.description}")
        print(f"   Input Token Limit: {model.input_token_limit:,}")
        print(f"   Output Token Limit: {model.output_token_limit:,}")
        print(f"   Supported Methods: {', '.join(model.supported_generation_methods)}")
        print("-" * 80)

print("\n✅ Recommended Models for Animation GenAI:")
print("   • gemini-2.0-flash-exp - Fast and efficient (RECOMMENDED)")
print("   • gemini-2.0-pro-exp - Most capable for complex animations")
print("   • gemini-1.5-flash - Stable and reliable")
print("   • gemini-1.5-pro - Balanced performance")

