import os
import django
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrosense_project.settings')
django.setup()

from core.models import Product

def populate_store():
    products_data = [
        # Fertilizers
        ('Urea 46% Nitrogen Fertilizer', 'Fertilizers', 500, 420, '50kg', False, 4.5, 'fertilizer bag'),
        ('DAP Premium (Diammonium Phosphate)', 'Fertilizers', 1500, 1350, '50kg', False, 4.7, 'DAP fertilizer'),
        ('MOP Potash Fertilizer', 'Fertilizers', 1200, 1050, '50kg', False, 4.4, 'potash fertilizer'),
        ('NPK 19:19:19 Soluble', 'Fertilizers', 250, 180, '1kg', False, 4.8, 'NPK fertilizer'),
        ('Zinc Sulphate Micronutrient', 'Fertilizers', 350, 290, '5kg', False, 4.6, 'zinc fertilizer'),

        # Seeds
        ('Hybrid Maize High-Yield Seeds', 'Seeds', 800, 650, '5kg', False, 4.9, 'maize seeds'),
        ('Basmati Paddy Seeds (Long Grain)', 'Seeds', 1200, 950, '10kg', False, 4.7, 'rice seeds'),
        ('F1 Hybrid Tomato Seeds', 'Seeds', 250, 200, '50g', False, 4.5, 'tomato seeds'),
        ('Bt Cotton BG-II Seeds', 'Seeds', 900, 750, '450g', False, 4.6, 'cotton seeds'),
        ('High-Yield Wheat Seeds', 'Seeds', 1800, 1600, '40kg', False, 4.8, 'wheat seeds'),

        # Pesticides
        ('Organic Neem Oil Insecticide', 'Pesticides', 450, 380, '1L', True, 4.7, 'neem oil bottle'),
        ('Broad Spectrum Herbicide', 'Pesticides', 600, 520, '1L', False, 4.3, 'pesticide bottle'),
        ('Systemic Fungicide (Bio)', 'Pesticides', 550, 480, '500g', False, 4.5, 'fungicide'),
        ('Insect Killer SL-17', 'Pesticides', 350, 290, '250ml', False, 4.6, 'insecticide spray'),

        # Tools
        ('Manual Knapsack Sprayer', 'Tools', 1800, 1550, '1 piece', False, 4.5, 'backpack sprayer'),
        ('Electric Battery Sprayer', 'Tools', 4500, 3800, '1 piece', False, 4.8, 'power sprayer'),
        ('Premium Steel Hand Hoe', 'Tools', 350, 280, '1 piece', False, 4.4, 'farming hoe'),
        ('Professional Pruning Shears', 'Tools', 550, 420, '1 piece', False, 4.7, 'garden shears'),

        # Organic
        ('Premium Vermicompost', 'Organic', 400, 320, '10kg', True, 4.9, 'compost soil'),
        ('Bio-Fertilizer Azotobacter', 'Organic', 150, 120, '1kg', True, 4.6, 'bio fertilizer'),
        ('Liquid Seaweed Extract', 'Organic', 600, 480, '1L', True, 4.8, 'liquid fertilizer'),

        # Irrigation
        ('Drip Irrigation Kit (Full Set)', 'Irrigation', 2500, 2100, '1 set', False, 4.6, 'drip irrigation'),
        ('Brass Impact Sprinkler', 'Irrigation', 450, 380, '1 piece', False, 4.5, 'water sprinkler'),
        ('Heavy Duty PVC Hose', 'Irrigation', 1500, 1200, '30m', False, 4.3, 'garden hose'),

        # Soil
        ('Digital Soil pH Meter', 'Soil', 1200, 950, '1 piece', False, 4.7, 'soil ph meter'),
        ('NPK Soil Testing Kit', 'Soil', 800, 650, '1 set', False, 4.5, 'soil testing'),
        
        # New Budget Plants
        ('Forest Tree Sapling (Teak/Neem)', 'Seeds', 5, 2, '1 plant', True, 4.8, 'young plant sapling'),
    ]

    # Stable Unsplash IDs for realistic farming products
    product_images = {
        'Urea 46% Nitrogen Fertilizer': '1585314062340-f1a5a7c9328d',
        'DAP Premium (Diammonium Phosphate)': '1628352081506-c1c4415fd7b2',
        'MOP Potash Fertilizer': '1559881433-3d02f9046097',
        'NPK 19:19:19 Soluble': '1591971737811-cf7ee8c4a931',
        'Zinc Sulphate Micronutrient': '1595009552197-230af320ac6a',
        'Hybrid Maize High-Yield Seeds': '1536631980041-7bb70a45634a',
        'Basmati Paddy Seeds (Long Grain)': '1523348837708-15d4a09cfac2',
        'F1 Hybrid Tomato Seeds': '1592533004055-27409ac68a1d',
        'Bt Cotton BG-II Seeds': '1500382017468-9049fed747ef',
        'High-Yield Wheat Seeds': '1501436028728-4a5f32002367',
        'Organic Neem Oil Insecticide': '1590682846337-083654406282',
        'Broad Spectrum Herbicide': '1605330867439-2701d844cdf7',
        'Systemic Fungicide (Bio)': '1615485243301-898a17ea3f1d',
        'Insect Killer SL-17': '1590682846337-083654406282',
        'Manual Knapsack Sprayer': '1589923188900-85dae5233427',
        'Electric Battery Sprayer': '1416870234185-d83ade3a65ea',
        'Premium Steel Hand Hoe': '1523301343973-018282434546',
        'Professional Pruning Shears': '1567171466-20d0496136d1',
        'Premium Vermicompost': '1542838132-92c53300491e',
        'Bio-Fertilizer Azotobacter': '1624477891295-603126f96280',
        'Liquid Seaweed Extract': '1550989460-0adf9ea622e2',
        'Drip Irrigation Kit (Full Set)': '1558449028-b53a39d100fc',
        'Brass Impact Sprinkler': '1563514227147-6d2ff66de8c4',
        'Heavy Duty PVC Hose': '1597401188473-b2955866f81e',
        'Digital Soil pH Meter': '1581273522201-923f6630f606',
        'NPK Soil Testing Kit': '1592288305644-4b5303975001',
        'Forest Tree Sapling (Teak/Neem)': '1501004318641-d39e6d0306f1',
    }

    Product.objects.all().delete()
    
    for name, category, mrp, price, qty, organic, rating, img_keyword in products_data:
        image_id = product_images.get(name, '1495107336214-bca9f1635f43')
        image_url = f"https://images.unsplash.com/photo-{image_id}?auto=format&fit=crop&w=600&q=80"

        Product.objects.create(
            name=name,
            category=category,
            mrp=mrp,
            price=price,
            quantity_weight=qty,
            is_organic=organic,
            rating=rating,
            image_url=image_url
        )

    print(f"Successfully populated {Product.objects.count()} products!")

if __name__ == '__main__':
    populate_store()
