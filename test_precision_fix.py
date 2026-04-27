#!/usr/bin/env python
import os
import django
import io
from PIL import Image
import numpy as np

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrosense_project.settings')
django.setup()

def create_test_image(main_color, defect_color=None, defect_ratio=0.05):
    """Create a test image with a main color and a local defect"""
    size = (100, 100)
    img_data = np.full((size[0], size[1], 3), main_color, dtype=np.uint8)
    
    if defect_color:
        # Add a local defect patch
        num_pixels = int(10000 * defect_ratio)
        side = int(np.sqrt(num_pixels))
        img_data[10:10+side, 10:10+side] = defect_color
        
    img = Image.fromarray(img_data)
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    return img_bytes

def test_precision_fix():
    print("Testing Precise Localized Defect Detection")
    print("=" * 60)
    
    from django.test import Client
    client = Client()
    
    # 1. Perfect Tomato
    print("\nCase 1: Perfect Red Tomato")
    img = create_test_image((210, 45, 45))
    res = client.post('/api/predict-fair-price/', {'crop': 'Tomato', 'file': img}).json()
    print(f"  Result: {res['quality']} (Score: {res['score']})")
    print(f"  Report: {res['report']}")
    
    # 2. Tomato with small Rot patch (5%)
    print("\nCase 2: Tomato with Rot patch (5%)")
    # Rot profile for tomato: (80, 120, 40, 80, 30, 60)
    img = create_test_image((210, 45, 45), defect_color=(100, 60, 45))
    res = client.post('/api/predict-fair-price/', {'crop': 'Tomato', 'file': img}).json()
    print(f"  Result: {res['quality']} (Score: {res['score']})")
    print(f"  Report: {res['report']}")
    
    # 3. Rice with Yellowing (5%)
    print("\nCase 3: Rice with Yellowing (5%)")
    # Yellowing profile for rice: (180, 220, 170, 210, 100, 150)
    img = create_test_image((240, 240, 220), defect_color=(200, 190, 120))
    res = client.post('/api/predict-fair-price/', {'crop': 'Rice', 'file': img}).json()
    print(f"  Result: {res['quality']} (Score: {res['score']})")
    print(f"  Report: {res['report']}")

if __name__ == "__main__":
    test_precision_fix()
