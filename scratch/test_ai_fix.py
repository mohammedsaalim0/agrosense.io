import requests
import os
import random
from PIL import Image
import io

def test_ai_precision():
    url = "http://127.0.0.1:8000/api/predict-fair-price/"
    
    # Test cases: (Crop, Color)
    tests = [
        ('Tomato', (210, 45, 45)), # Perfect Tomato
        ('Tomato', (100, 45, 45)), # Dark/Bruised Tomato
        ('Rice', (180, 185, 160)), # Perfect Rice
        ('Wheat', (100, 100, 100)) # Grey/Damaged Wheat
    ]
    
    for crop, color in tests:
        img = Image.new('RGB', (100, 100), color=color)
        buf = io.BytesIO()
        img.save(buf, format='JPEG')
        buf.seek(0)
        
        files = {'file': (f'test.jpg', buf, 'image/jpeg')}
        data = {'crop': crop}
        
        print(f"Testing {crop} with color {color}...")
        try:
            response = requests.post(url, files=files, data=data)
            res = response.json()
            print(f"  Result: {res['quality']} ({res['score']}/100)")
            print(f"  Proof: {res['visual_proof']}")
            print(f"  Report: {res['report']}")
        except Exception as e:
            print(f"  Error: {e}")
        print("-" * 30)

if __name__ == "__main__":
    test_ai_precision()
