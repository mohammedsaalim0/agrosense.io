import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrosense_project.settings')
django.setup()

from core.models import SupportScheme, MarketListing

def populate():
    # Schemes
    schemes = [
        ('PM-Kisan Samman Nidhi', 'Central Govt', 'SUB', '₹6,000 / Year', 'Direct income support for small and marginal farmers.'),
        ('PM Fasal Bima Yojana', 'MoA&FW', 'INS', 'Low Premium', 'Comprehensive insurance cover against crop failure.'),
        ('Agri-Clinic Loans', 'NABARD', 'LOAN', 'Up to ₹20 Lakh', 'Financial assistance for setting up agricultural ventures.'),
        ('Soil Health Card', 'State Govt', 'SUB', 'Free Analysis', 'Get detailed report on soil nutrient status.'),
        ('Kisan Credit Card', 'Public Banks', 'LOAN', 'Low Interest', 'Hassle-free short term credit for cultivation.'),
        ('Solar Pump Subsidy', 'PM-KUSUM', 'SUB', '60% Subsidy', 'Financial aid for installing solar water pumps.'),
    ]

    for title, provider, stype, amount, desc in schemes:
        SupportScheme.objects.get_or_create(
            title=title,
            provider=provider,
            scheme_type=stype,
            amount=amount,
            description=desc
        )

    # Listings
    listings = [
        ('Basmati Rice', 3500.00, '100 Quintals', 'Rajesh Kumar', 'Amritsar, Punjab'),
        ('Cotton', 7200.00, '40 Quintals', 'Sanjay Patil', 'Nagpur, Maharashtra'),
        ('Wheat', 2400.00, '150 Quintals', 'Gurpreet Singh', 'Ludhiana, Punjab'),
        ('Maize', 2150.00, '80 Quintals', 'Amit Sharma', 'Bareilly, UP'),
        ('Soybean', 4800.00, '60 Quintals', 'Deepak Verma', 'Indore, MP'),
    ]

    for crop, price, qty, seller, loc in listings:
        MarketListing.objects.get_or_create(
            crop_name=crop,
            price=price,
            quantity=qty,
            seller_name=seller,
            location=loc
        )

    print("Database populated successfully!")

if __name__ == '__main__':
    populate()
