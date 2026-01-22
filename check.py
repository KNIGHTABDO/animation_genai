from google import genai
import os
from dotenv import load_dotenv

# Load API key
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ Error: GOOGLE_API_KEY or GEMINI_API_KEY not found in .env file")
    exit(1)

client = genai.Client(api_key=api_key)

print("🔍 Available Gemini Models:\n")
print("=" * 80)

try:
    models = client.models.list()
    for model in models:
        print(f"\n📦 Model: {model.name}")
        if hasattr(model, 'display_name'):
            print(f"   Display Name: {model.display_name}")
        if hasattr(model, 'description'):
            print(f"   Description: {model.description}")
        print("-" * 80)
except Exception as e:
    print(f"Error listing models: {e}")
    print("\nNote: The new google-genai SDK may have different model listing capabilities.")

print("\n✅ Recommended Models for Animation GenAI:")
print("   • gemini-3-flash-preview - Newest with advanced thinking (RECOMMENDED)")
print("   • gemini-2.0-flash-exp - Fast and efficient")
print("   • gemini-1.5-flash - Stable and reliable")
print("   • gemini-1.5-pro - Balanced performance")


