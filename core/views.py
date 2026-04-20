from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login as auth_login
from django.http import JsonResponse
from .models import Crop, SupportScheme, MarketListing, SchemeApplication, Profile
import random

@login_required
def dashboard(request):
    schemes = SupportScheme.objects.all()[:6]
    listings = MarketListing.objects.all().order_by('-created_at')[:5]
    applications = SchemeApplication.objects.filter(user=request.user).order_by('-applied_at')
    context = {
        'schemes': schemes,
        'listings': listings,
        'applications': applications,
    }
    return render(request, 'core/dashboard.html', context)

def api_apply_scheme(request):
    if request.method == 'POST' and request.user.is_authenticated:
        scheme_name = request.POST.get('scheme_name')
        # Check if already applied
        if SchemeApplication.objects.filter(user=request.user, scheme_name=scheme_name).exists():
            return JsonResponse({'status': 'exists', 'message': 'You have already applied for this scheme.'}, status=200)
            
        SchemeApplication.objects.create(user=request.user, scheme_name=scheme_name)
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

def api_cancel_application(request):
    if request.method == 'POST' and request.user.is_authenticated:
        scheme_name = request.POST.get('scheme_name')
        # Find and delete
        app = SchemeApplication.objects.filter(user=request.user, scheme_name=scheme_name).first()
        if app:
            app.delete()
            return JsonResponse({'status': 'success'})
        return JsonResponse({'status': 'error', 'message': 'Application not found'}, status=404)
    return JsonResponse({'status': 'error'}, status=400)

def api_recommend(request):
    state = request.GET.get('state', '')
    soil = request.GET.get('soil', '')
    season = request.GET.get('season', '')
    
    # Deterministic Seed based on input string
    seed_str = f"{state}{soil}{season}"
    random.seed(seed_str)
    
    # AI Recommendation Logic
    crops = [
        {'name': 'Basmati Rice', 'score': random.randint(85, 98), 'yield': round(random.uniform(3.5, 5.0), 1)},
        {'name': 'Organic Wheat', 'score': random.randint(80, 95), 'yield': round(random.uniform(4.0, 6.0), 1)},
        {'name': 'Golden Maize', 'score': random.randint(75, 90), 'yield': round(random.uniform(3.0, 4.5), 1)},
        {'name': 'Long Staple Cotton', 'score': random.randint(70, 88), 'yield': round(random.uniform(2.0, 3.5), 1)},
    ]
    # Reset seed for other functions
    random.seed(None)
    return JsonResponse({'crops': crops})

def api_market_data(request):
    crop = request.GET.get('crop', 'Wheat').lower()
    random.seed(crop) # Same crop always has same base trend
    
    # Market Data
    trends = [random.randint(2000, 2500) for _ in range(12)]
    metrics = {
        'demand': random.randint(60, 95),
        'supply': random.randint(30, 70),
        'profit': random.randint(50, 90)
    }
    stability = [random.randint(60, 100) for _ in range(5)]
    random.seed(None)
    return JsonResponse({
        'trends': trends,
        'metrics': metrics,
        'stability': stability
    })

def api_scan(request):
    filename = request.GET.get('filename', '').lower()
    date_str = request.GET.get('date', '')
    
    # Supported image extensions
    image_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.heic']
    is_image = any(filename.endswith(ext) for ext in image_extensions)
    
    # Simulate Plant Detection via keyword checking
    plant_keywords = ['leaf', 'plant', 'rice', 'wheat', 'maize', 'cotton', 'crop', 'tree', 'field', 'nature', 'green', 'agriculture', 'img_', 'dsc_']
    is_plant_keyword = any(kw in filename for kw in plant_keywords)
    
    if not is_image and not is_plant_keyword:
        return JsonResponse({
            'status': 'error',
            'message': 'AI Vision: Non-plant object detected or unsupported format. Please upload a clear photo of a crop or plant leaf.'
        }, status=400)

    # Deterministic Seed based on file and date
    random.seed(f"{filename}{date_str}")
    
    # Identification Logic
    detected_plant = 'Rice (Oryza sativa)'
    if 'wheat' in filename: 
        detected_plant = 'Wheat (Triticum aestivum)'
    elif 'maize' in filename: 
        detected_plant = 'Maize (Zea mays)'
    elif 'cotton' in filename: 
        detected_plant = 'Cotton (Gossypium)'
    elif 'leaf' in filename or 'plant' in filename:
        detected_plant = random.choice(['Tomato (Solanum lycopersicum)', 'Potato (Solanum tuberosum)', 'Chili (Capsicum annuum)'])
    else:
        # Fallback for generic phone uploads like IMG_1234.jpg
        detected_plant = random.choice(['Rice (Oryza sativa)', 'Wheat (Triticum aestivum)', 'Maize (Zea mays)', 'Soybean (Glycine max)'])

    results = {
        'status': 'success',
        'plant': detected_plant,
        'health': random.choice(['Healthy', 'Minor Stress', 'Thriving']),
        'growth': random.randint(50, 95),
        'health_radar': [random.randint(60, 100) for _ in range(5)],
        'disease_risk': random.randint(1, 12),
        'chlorophyll': [random.randint(40, 98) for _ in range(7)]
    }
    random.seed(None)
    return JsonResponse(results)

def api_create_listing(request):
    if request.method == 'POST':
        crop = request.POST.get('crop')
        qty = request.POST.get('quantity')
        price = request.POST.get('price')
        
        # Save to real database
        listing = MarketListing.objects.create(
            crop_name=crop,
            quantity=f"{qty} Quintals",
            price=price,
            seller_name=request.user.username,
            location="User Location" # In real app, would come from profile
        )
        return JsonResponse({
            'status': 'success', 
            'listing': {
                'crop_name': listing.crop_name,
                'price': float(listing.price),
                'quantity': listing.quantity,
                'seller_name': listing.seller_name
            }
        })
    return JsonResponse({'status': 'error'}, status=400)

def api_remove_listing(request):
    if request.method == 'POST' and request.user.is_authenticated:
        listing_id = request.POST.get('listing_id')
        try:
            listing = MarketListing.objects.get(id=listing_id)
            listing.delete()
            return JsonResponse({'status': 'success'})
        except MarketListing.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Listing not found'}, status=404)
    return JsonResponse({'status': 'error'}, status=400)

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        dob = request.POST.get('dob')
        profession = request.POST.get('profession')
        
        if form.is_valid():
            user = form.save()
            user.first_name = first_name
            user.last_name = last_name
            user.save()
            
            # Create profile
            Profile.objects.create(user=user, dob=dob, profession=profession)
            
            auth_login(request, user)
            return redirect('dashboard')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})
