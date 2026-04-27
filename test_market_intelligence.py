#!/usr/bin/env python
import os
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrosense_project.settings')
django.setup()

def test_market_intelligence():
    """Test Market Intelligence for various crop types"""
    
    print("Testing Market Intelligence for All Crop Types")
    print("=" * 60)
    
    # Test cases covering different crop categories
    test_crops = [
        # Cereals & Grains
        'wheat', 'rice', 'maize', 'jowar', 'bajra', 'ragi', 'barley',
        # Cash Crops  
        'cotton', 'sugarcane', 'tobacco', 'coffee', 'tea',
        # Pulses
        'tur', 'moong', 'urad', 'arhar',
        # Oilseeds
        'mustard', 'soyabean', 'groundnut', 'sunflower', 'sesamum',
        # Vegetables
        'tomato', 'potato', 'onion', 'chilli', 'garlic', 'ginger',
        # Spices
        'turmeric', 'coriander', 'cumin', 'pepper',
        # Unknown crops (should use category fallback)
        'millet', 'lentil', 'beans'
    ]
    
    from django.test import Client
    client = Client()
    
    success_count = 0
    total_count = len(test_crops)
    
    for crop in test_crops:
        try:
            response = client.get(f'/api/market-data/?crop={crop}')
            
            if response.status_code == 200:
                data = response.json()
                if data['status'] == 'success':
                    price = data['current_price']
                    intel = data['market_intel']
                    trends = data['trends'][:3]  # First 3 months
                    
                    print(f"✅ {crop.title()}: ₹{price}/quintal | {intel[:50]}...")
                    success_count += 1
                else:
                    print(f"❌ {crop.title()}: API returned error - {data.get('message', 'Unknown error')}")
            else:
                print(f"❌ {crop.title()}: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ {crop.title()}: Exception - {str(e)}")
    
    print("\n" + "=" * 60)
    print(f"Results: {success_count}/{total_count} crops working successfully")
    print(f"Success Rate: {(success_count/total_count)*100:.1f}%")
    
    if success_count == total_count:
        print("🎉 All crops are now supported in Market Intelligence!")
    else:
        print(f"⚠️  {total_count - success_count} crops still need attention")

if __name__ == "__main__":
    test_market_intelligence()
