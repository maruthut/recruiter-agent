import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Configure Gemini API
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("Error: GOOGLE_API_KEY not found in .env")
    exit(1)

genai.configure(api_key=api_key)

# List available models
print("Available Gemini models:")
try:
    models = genai.list_models()
    for model in models:
        print(f"- {model.name}")
except Exception as e:
    print(f"Error listing models: {e}")
    exit(1)

# Test a simple generation with a common model
test_model = "models/gemini-1.5-flash"  # Try a common one first
try:
    model = genai.GenerativeModel(test_model)
    response = model.generate_content("Hello, test message.")
    print(f"\nTest generation with {test_model}: {response.text}")
except Exception as e:
    print(f"Error with {test_model}: {e}")

# Suggest an appropriate model for this task (text-based agent)
print("\nRecommended model for HR Agent: Use 'models/gemini-1.5-flash' or 'models/gemini-1.5-pro' for balanced performance and cost.")