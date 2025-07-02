import os
import google.generativeai as genai

# Ensure your API key is set in environment variables, or replace directly
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    api_key = "YOUR_GEMINI_API_KEY" # Replace with your actual API Key if not in env

try:
    if api_key == "YOUR_GEMINI_API_KEY" or not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set or placeholder used. Please configure your API key.")

    genai.configure(api_key=api_key)
    print("Gemini API configured. Listing available models:")

    for m in genai.list_models():
        # Filter for models that support text generation (like 'generateContent')
        if 'generateContent' in m.supported_generation_methods:
            print(f"  Model Name: {m.name}")
            print(f"  Description: {m.description}")
            print(f"  Supported Methods: {m.supported_generation_methods}")
            print("-" * 30)

except Exception as e:
    print(f"An error occurred: {e}")