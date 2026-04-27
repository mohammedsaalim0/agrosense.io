#!/usr/bin/env python
import os
import django
import io
from PIL import Image
import numpy as np

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrosense_project.settings')
django.setup()

def create_test_image(color_profile, size=(200, 200)):
    """Create a test image with specific color profile"""
    img = Image.new('RGB', size, color=color_profile)
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    return img_bytes

def test_prediction_algorithm():
    """Test the improved crop prediction algorithm"""
    
    print("Testing Improved Crop Quality Prediction Algorithm")
    print("=" * 60)
    
    # Test cases for different crop qualities
    test_cases = [
        {
            'crop': 'tomato',
            'color': (200, 50, 30),  # Good tomato color
            'expected_quality': 'A-Grade or Premium'
        },
        {
            'crop': 'tomato', 
            'color': (100, 120, 40),  # Unripe tomato
            'expected_quality': 'Low or Standard'
        },
        {
            'crop': 'wheat',
            'color': (195, 170, 90),  # Good wheat color
            'expected_quality': 'A-Grade or Premium'
        },
        {
            'crop': 'wheat',
            'color': (130, 120, 80),  # Poor wheat color
            'expected_quality': 'Low or Standard'
        },
        {
            'crop': 'rice',
            'color': (210, 210, 190),  # Good rice color
            'expected_quality': 'A-Grade or Premium'
        }
    ]
    
    from django.test import Client
    client = Client()
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}: {test_case['crop'].title()} - Expected: {test_case['expected_quality']}")
        print(f"Color Profile: RGB{test_case['color']}")
        
        # Create test image
        img_bytes = create_test_image(test_case['color'])
        
        # Test the prediction endpoint
        response = client.post('/api/predict-fair-price/', {
            'crop': test_case['crop'],
            'file': img_bytes
        })
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Prediction: {result['quality']} (Score: {result['score']})")
            print(f"📊 Fair Price: ₹{result['fair_price']} (MSP: ₹{result['msp']})")
            print(f"📝 Report: {', '.join(result['report'][:2])}")
        else:
            print(f"❌ Error: {response.status_code} - {response.content.decode()}")
    
    print("\n" + "=" * 60)
    print("Test completed. The improved algorithm should now provide more accurate predictions.")

if __name__ == "__main__":
    test_prediction_algorithm()
