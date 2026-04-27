import os
import google.generativeai as genai
from PIL import Image
import io
import json
import re
from dotenv import load_dotenv
load_dotenv()

def find_working_model():
    api_key = os.environ.get('GOOGLE_API_KEY')
    if not api_key:
        print("ERROR: NO API KEY")
        return

    genai.configure(api_key=api_key)
    img = Image.new('RGB', (100, 100), color=(0, 255, 0))
    prompt = "Return JSON {'status': 'ok'}"
    
    # Priority list for "Super Accuracy"
    models_to_try = [
        'gemini-1.5-flash',
        'gemini-1.5-pro',
        'gemini-flash-latest',
        'gemini-2.0-flash',
        'gemini-pro-vision' # Legacy fallback
    ]
    
    for model_name in models_to_try:
        print(f"Testing {model_name}...")
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content([prompt, img])
            print(f"  SUCCESS! Response: {response.text[:50]}...")
            return model_name
        except Exception as e:
            print(f"  FAILED: {str(e)[:100]}")
    
    return None

if __name__ == "__main__":
    winner = find_working_model()
    print(f"\nWINNER: {winner}")
