import os
import google.generativeai as genai
from PIL import Image
import io
import json
import re

# Load .env manually if needed or assume it's in env
from dotenv import load_dotenv
load_dotenv()

def test_gemini_real():
    api_key = os.environ.get('GOOGLE_API_KEY')
    if not api_key:
        print("ERROR: GOOGLE_API_KEY not found in environment.")
        return

    print(f"Using API Key: {api_key[:10]}...")
    genai.configure(api_key=api_key)
    
    try:
        model = genai.GenerativeModel('gemini-flash-latest')
        
        # Create a dummy image (e.g. a red square)
        img = Image.new('RGB', (100, 100), color=(255, 0, 0))
        
        prompt = (
            "Analyze this crop image (red square). "
            "Respond ONLY in valid JSON: "
            "{\"quality\": \"Premium\", \"score\": 95, \"visual_proof\": \"Deep crimson color\", \"report\": [\"No defects\"], \"summary\": \"Healthy\", \"analysis\": \"High demand\"}"
        )
        
        print("Calling Gemini 1.5 Flash...")
        response = model.generate_content([prompt, img])
        res_text = response.text.strip()
        print(f"RAW RESPONSE: {res_text}")
        
        json_match = re.search(r'\{.*\}', res_text, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group(0))
            print("Successfully parsed JSON!")
            print(json.dumps(data, indent=2))
        else:
            print("Failed to find JSON in response.")
            
    except Exception as e:
        print(f"GEMINI ERROR: {str(e)}")

if __name__ == "__main__":
    test_gemini_real()
