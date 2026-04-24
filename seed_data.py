import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrosense_project.settings')
django.setup()

from core.models import SupportScheme, Product

def seed():
    print("🌱 Seeding essential data...")
    
    # Seed Support Schemes if empty
    if SupportScheme.objects.count() == 0:
        schemes = [
            {"title": "PM-Kisan Samman Nidhi", "description": "Direct income support of ₹6000 per year to farmers.", "provider": "Central Govt", "amount": "₹6,000/yr", "scheme_type": "Direct Benefit"},
            {"title": "PM Fasal Bima Yojana", "description": "Comprehensive insurance cover against crop failure.", "provider": "Govt of India", "amount": "Varies", "scheme_type": "Insurance"},
            {"title": "Soil Health Card Scheme", "description": "Helping farmers improve productivity through soil analysis.", "provider": "Agriculture Dept", "amount": "Free Service", "scheme_type": "Technical"},
        ]
        for s in schemes:
            SupportScheme.objects.create(**s)
        print("✅ Schemes seeded.")

    # Seed Products if empty
    if Product.objects.count() == 0:
        products = [
            {"name": "Organic Vermicompost", "description": "High-quality organic manure for better soil health.", "price": 450, "category": "Fertilizer", "pack_size": "50kg"},
            {"name": "Hybrid Wheat Seeds", "description": "High-yield drought-resistant wheat variety.", "price": 1200, "category": "Seeds", "pack_size": "20kg"},
            {"name": "NPK 19:19:19", "description": "Water-soluble fertilizer for all crops.", "price": 850, "category": "Fertilizer", "pack_size": "25kg"},
        ]
        for p in products:
            Product.objects.create(**p)
        print("✅ Products seeded.")

if __name__ == "__main__":
    seed()
