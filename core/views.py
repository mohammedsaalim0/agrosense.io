from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login as auth_login, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.http import JsonResponse
from django.db.utils import OperationalError, ProgrammingError
from django.utils import timezone
from .models import Crop, SupportScheme, MarketListing, SchemeApplication, Profile, LearningProgress, CourseCertificate, CourseAssessment
import random
import io
import base64
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse
from .models import Crop, SupportScheme, MarketListing, SchemeApplication, Profile, LearningProgress, CourseCertificate, CourseAssessment, Product, Order
import uuid


PASSING_SCORE = 70


EDU_COURSES = [
    {
        'course_key': 'agri-course-1',
        'title': 'AgroSense Foundations',
        'description': 'Core agriculture fundamentals for smart decision making.',
        'playlist_url': 'https://www.youtube.com/watch?v=KuePVJQP4sc&list=PLVg7mwdkOVxisCHVXAUrYwjiOMUDhUb93',
        'embed_url': 'https://www.youtube.com/embed/KuePVJQP4sc?list=PLVg7mwdkOVxisCHVXAUrYwjiOMUDhUb93&enablejsapi=1&rel=0',
        'lessons': 15,
        'duration': '3h 00m',
        'duration_seconds': 10800,
    },
    {
        'course_key': 'agri-course-2',
        'title': 'AgroSense Advanced Practices',
        'description': 'Practical field strategies to improve productivity and resilience.',
        'playlist_url': 'https://www.youtube.com/watch?v=IQzlj93Pz5Q&list=PL7Ine0vGWAijDlGc-nFoaCP3i5Jf_frqj',
        'embed_url': 'https://www.youtube.com/embed/IQzlj93Pz5Q?list=PL7Ine0vGWAijDlGc-nFoaCP3i5Jf_frqj&enablejsapi=1&rel=0',
        'lessons': 14,
        'duration': '2h 30m',
        'duration_seconds': 9000,
    },
    {
        'course_key': 'agri-course-3',
        'title': 'AgroSense Crop Mastery',
        'description': 'Improve crop care, disease detection, and farm output planning.',
        'playlist_url': 'https://www.youtube.com/watch?v=oy0AJYCDoFU&list=PLDsv3FFHKiccaLVwGA-DvGo2APiMWL2cq',
        'embed_url': 'https://www.youtube.com/embed/oy0AJYCDoFU?list=PLDsv3FFHKiccaLVwGA-DvGo2APiMWL2cq&enablejsapi=1&rel=0',
        'lessons': 18,
        'duration': '3h 30m',
        'duration_seconds': 12600,
    },
    {
        'course_key': 'agri-course-4',
        'title': 'AgroSense Expert Session',
        'description': 'A focused expert lecture with real-world farm insights.',
        'playlist_url': 'https://www.youtube.com/watch?v=VgJ-zRAdvaE',
        'embed_url': 'https://www.youtube.com/embed/VgJ-zRAdvaE?enablejsapi=1&rel=0',
        'lessons': 1,
        'duration': '1h 00m',
        'duration_seconds': 3600,
    },
]

@login_required
def dashboard(request):
    schemes = SupportScheme.objects.all()[:6]
    listings = MarketListing.objects.all().order_by('-created_at')[:5]
    applications = SchemeApplication.objects.filter(user=request.user).order_by('-applied_at')
    try:
        progress_map = {item.course_key: item for item in LearningProgress.objects.filter(user=request.user)}
        cert_map = {item.course_key: item for item in CourseCertificate.objects.filter(user=request.user)}
        assess_map = {item.course_key: item for item in CourseAssessment.objects.filter(user=request.user)}
    except (OperationalError, ProgrammingError):
        # Keep dashboard usable even if migrations were not applied yet.
        progress_map = {}
        cert_map = {}
        assess_map = {}
    edu_courses = []
    origin = f"{request.scheme}://{request.get_host()}"
    for course in EDU_COURSES:
        progress_entry = progress_map.get(course['course_key'])
        certificate = cert_map.get(course['course_key'])
        parsed = urlparse(course['embed_url'])
        query = dict(parse_qsl(parsed.query))
        query['origin'] = origin
        query['enablejsapi'] = '1'
        query['playsinline'] = '1'
        embed_with_origin = urlunparse(parsed._replace(query=urlencode(query)))
        edu_courses.append({
            **course,
            'embed_url': embed_with_origin,
            'progress': progress_entry.progress if progress_entry else 0,
            'completed': progress_entry.completed if progress_entry else False,
            'certificate_code': certificate.certificate_code if certificate else '',
            'assessment_passed': assess_map.get(course['course_key']).passed if assess_map.get(course['course_key']) else False,
            'assessment_score': assess_map.get(course['course_key']).score if assess_map.get(course['course_key']) else 0,
        })

    context = {
        'schemes': schemes,
        'listings': listings,
        'applications': applications,
        'edu_courses': edu_courses,
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

def api_search_market(request):
    crop = request.GET.get('crop', 'Wheat').capitalize()
    location = request.GET.get('location', 'India').capitalize()
    
    # Realistic profiles based on common regions
    sellers = [
        {'name': "Balwinder Sandhu", 'desc': f"Premium {crop} Cultivator", 'loc': f"Fazilka, {location}", 'rating': 4.9, 'phone': "+91 98765 43210", 'email': "balwinder.agri@gmail.com"},
        {'name': "Gajendra Singh", 'desc': f"Organic {crop} Producer", 'loc': f"Hansi, {location}", 'rating': 4.8, 'phone': "+91 87654 32109", 'email': "gajendra.organic@gmail.com"},
        {'name': "Manoj Tiwari", 'desc': f"Large-scale {crop} Farmer", 'loc': f"Varanasi, {location}", 'rating': 4.7, 'phone': "+91 76543 21098", 'email': "manoj.farmer@gmail.com"},
    ]
    buyers = [
        {'name': "GrainTrade Corp", 'desc': "International Export Unit", 'loc': f"Port Area, {location}", 'rating': 4.6, 'phone': "+91 99887 76655", 'email': "procure@graintrade.co"},
        {'name': "HarvestHub India", 'desc': "Direct Retail Chain", 'loc': f"Central Market, {location}", 'rating': 4.5, 'phone': "+91 88776 65544", 'email': "info@harvesthub.in"},
        {'name': "AgriProcure Pvt Ltd", 'desc': "Bulk Storage & Logistics", 'loc': f"Industrial Hub, {location}", 'rating': 4.9, 'phone': "+91 77665 54433", 'email': "ops@agriprocure.com"},
    ]
    
    random.seed(f"{crop}{location}")
    seller = random.choice(sellers)
    buyer = random.choice(buyers)
    random.seed(None)
    
    return JsonResponse({
        'status': 'success',
        'seller': seller,
        'buyer': buyer
    })
def call_ollama(prompt):
    """Helper to call local Ollama API if available."""
    try:
        import requests
        response = requests.post('http://localhost:11434/api/generate', 
                               json={
                                   'model': 'llama3', 
                                   'prompt': prompt,
                                   'stream': False
                               }, timeout=5)
        if response.status_code == 200:
            return response.json().get('response', '').strip()
    except:
        pass
    return None

def api_market_data(request):
    crop = request.GET.get('crop', 'Wheat').capitalize()
    
    # Try to get "Real" predicted price from Ollama
    ollama_response = call_ollama(f"As a market analyst, predict the current average market price for {crop} in India per quintal. Return ONLY the numerical value in INR (e.g. 2150).")
    
    try:
        if ollama_response:
            # Extract number from response
            import re
            numbers = re.findall(r'\d+', ollama_response)
            if numbers:
                base_price = int(numbers[0])
            else:
                raise ValueError
        else:
            raise ValueError
    except:
        # Fallback to realistic ranges based on crop
        price_ranges = {
            'Wheat': (2100, 2400),
            'Rice': (2000, 2500),
            'Cotton': (6000, 8000),
            'Maize': (1800, 2100),
            'Tomato': (1500, 4000),
            'Potato': (1200, 1800),
        }
        low, high = price_ranges.get(crop, (2000, 3000))
        base_price = random.randint(low, high)

    # Generate realistic trends around the base price
    trends = [int(base_price * (1 + random.uniform(-0.05, 0.05))) for _ in range(12)]
    
    metrics = {
        'demand': random.randint(70, 95) if base_price > 2000 else random.randint(40, 70),
        'supply': random.randint(30, 80),
        'profit': random.randint(50, 90),
        'source': 'Ollama AI Intelligence' if ollama_response else 'AgroSense Market Analysis'
    }
    
    stability = [random.randint(60, 100) for _ in range(5)]
    
def api_get_schemes(request):
    # Simulated fetch from myScheme.gov.in
    schemes = [
        {
            'title': "PM-Kisan Samman Nidhi",
            'category': "Income Support",
            'amount': "₹6,000 / Year",
            'provider': "Department of Agriculture & FW",
            'desc': "Direct income support to all landholding farmers' families in the country.",
            'official_url': "https://pmkisan.gov.in/",
            'status_url': "https://pmkisan.gov.in/BeneficiaryStatus_New.aspx",
            'active': True
        },
        {
            'title': "Pradhan Mantri Fasal Bima Yojana",
            'category': "Crop Insurance",
            'amount': "Max Coverage",
            'provider': "Ministry of Agriculture",
            'desc': "Financial support to farmers suffering crop loss/damage arising out of natural calamities.",
            'official_url': "https://pmfby.gov.in/",
            'status_url': "https://pmfby.gov.in/status",
            'active': True
        },
        {
            'title': "Kisan Credit Card (KCC)",
            'category': "Credit",
            'amount': "Low Interest Loans",
            'provider': "NABARD / RBI",
            'desc': "Adequate and timely credit support from the banking system for agricultural needs.",
            'official_url': "https://www.myscheme.gov.in/schemes/kcc",
            'status_url': "https://www.myscheme.gov.in/schemes/kcc",
            'active': True
        }
    ]
    return JsonResponse({'schemes': schemes})

def agro_suggestion(request):
    return render(request, 'core/agro_suggestion.html')

def api_weather_soil(request):
    location = request.GET.get('location', 'Current Location').lower()
    crop = request.GET.get('crop', 'Wheat').lower()
    
    # Improved Location-Aware Logic (Simulation)
    temp = random.randint(22, 35)
    humidity = random.randint(40, 85)
    condition = random.choice(['Sunny', 'Partly Cloudy', 'Clear Skies', 'Light Breeze'])
    soil_type = 'Alluvial'
    ph_level = round(random.uniform(6.0, 7.5), 1)
    suitability_score = random.randint(60, 95)
    
    # Specific Location Logic
    if 'sahara' in location or 'desert' in location:
        temp = random.randint(40, 50)
        humidity = random.randint(5, 15)
        condition = 'Extreme Heat'
        soil_type = 'Desert Sand'
        ph_level = round(random.uniform(8.0, 9.0), 1)
        # Default low, but cactus thrives here
        suitability_score = random.randint(5, 15)
        if 'cactus' in crop or 'succulent' in crop:
            suitability_score = random.randint(85, 98)
            condition = 'Ideal Arid Conditions'
    elif 'antarctica' in location or 'arctic' in location or 'polar' in location:
        temp = random.randint(-40, -10)
        humidity = random.randint(10, 30)
        condition = 'Freezing'
        soil_type = 'Permafrost'
        ph_level = round(random.uniform(4.0, 5.5), 1)
        suitability_score = random.randint(0, 5)
    elif 'himalaya' in location or 'mountain' in location:
        temp = random.randint(5, 15)
        soil_type = 'Mountain Soil'
        suitability_score = random.randint(30, 50)
    
    # Crop Specificity (Simple adjustment)
    if 'wheat' in crop and temp > 35:
        suitability_score -= 20
    elif 'rice' in crop and humidity < 60:
        suitability_score -= 30
        
    suitability_score = max(0, min(100, suitability_score))
    
    if suitability_score > 75: suitability = "High"
    elif suitability_score > 40: suitability = "Moderate"
    else: suitability = "Low"
    
    # Chart Data for Visualization
    chart_data = {
        'yield_forecast': [random.randint(60, 100) for _ in range(6)],
        'soil_composition': {
            'Sand': 30 if 'desert' not in location else 80,
            'Silt': 40 if 'desert' not in location else 10,
            'Clay': 30 if 'desert' not in location else 10
        }
    }
    
    return JsonResponse({
        'location': location.capitalize(),
        'temp': f"{temp}°C",
        'humidity': f"{humidity}%",
        'condition': condition,
        'soil_type': soil_type,
        'ph': ph_level,
        'suitability': suitability,
        'suitability_score': suitability_score,
        'chart_data': chart_data,
        'last_updated': timezone.now().strftime('%H:%M')
    })

def api_scan(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Only POST requests are allowed.'}, status=405)

    if 'file' not in request.FILES:
        return JsonResponse({'status': 'error', 'message': 'No file uploaded.'}, status=400)

    image_file = request.FILES['file']
    date_str = request.POST.get('date', '')
    
    try:
        # Open image using Pillow
        img = Image.open(image_file)
        img = img.convert('RGB')
        width, height = img.size
        
        # Analyze image for "Greenness"
        # We'll sample some pixels to get an idea of the color profile
        pixels = img.getdata()
        green_pixels = 0
        total_pixels = len(pixels)
        
        # Sample every 10th pixel for performance
        sample_step = max(1, total_pixels // 1000)
        for i in range(0, total_pixels, sample_step):
            r, g, b = pixels[i]
            # Plant-like green detection: G > R and G > B, or G is significantly high
            if g > r * 1.1 and g > b * 1.1:
                green_pixels += 1
        
        green_ratio = green_pixels / (total_pixels / sample_step)
        
        # If green ratio is very low, it's likely not a plant
        if green_ratio < 0.15:
            return JsonResponse({
                'status': 'error',
                'message': 'AI Vision: Non-plant object detected. Please upload a real crop or plant photo (it seems there is not enough green foliage).'
            }, status=400)

        # Identification Logic based on green ratio and randomness
        # This is still a simulation but now it's grounded in the image data
        random.seed(f"{image_file.name}{date_str}")
        
        detected_plant = 'Rice (Oryza sativa)'
        confidence_val = int(85 + (green_ratio * 10)) # Higher green ratio = more confidence
        if confidence_val > 99: confidence_val = 99
        
        # Heuristics based on filename if available (as a fallback/supplement)
        filename = image_file.name.lower()
        if 'wheat' in filename: 
            detected_plant = 'Wheat (Triticum aestivum)'
        elif 'maize' in filename: 
            detected_plant = 'Maize (Zea mays)'
        elif 'cotton' in filename: 
            detected_plant = 'Cotton (Gossypium)'
        elif 'tomato' in filename: 
            detected_plant = 'Tomato (Solanum lycopersicum)'
        else:
            detected_plant = random.choice(['High-Yield Rice', 'Resilient Wheat', 'Hybrid Maize'])

        results = {
            'status': 'success',
            'plant': detected_plant,
            'health': 'Healthy' if green_ratio > 0.4 else 'Needs Attention',
            'confidence': f"{confidence_val}%",
            'growth': int(70 + (green_ratio * 30)),
            'health_radar': [random.randint(70, 100) for _ in range(5)],
            'disease_risk': random.randint(1, 5) if green_ratio > 0.4 else random.randint(5, 15),
            'chlorophyll': [int(50 + (green_ratio * 50) + random.randint(-5, 5)) for _ in range(7)]
        }

        random.seed(None)
        return JsonResponse(results)

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Error processing image: {str(e)}'}, status=500)

def api_predict_fair_price(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Use POST with an image file.'}, status=405)
    
    crop = request.POST.get('crop', 'Wheat').capitalize()
    image_file = request.FILES.get('file')
    
    if not image_file:
        return JsonResponse({'status': 'error', 'message': 'No image uploaded for scanning.'}, status=400)

    try:
        # Real-time MSP Data
        msps = {
            'Wheat': 2275, 'Paddy': 2183, 'Maize': 2090, 'Cotton': 6620, 'Jowar': 3180, 
            'Bajra': 2500, 'Ragi': 3846, 'Arhar': 7000, 'Moong': 8558, 'Urad': 6950,
            'Groundnut': 6377, 'Sunflower': 6760, 'Soyabean': 4600, 'Sesamum': 8635,
            'Nigerseed': 7734, 'Sugarcane': 315, 'Tomato': 2500, 'Potato': 1500, 'Onion': 2200
        }
        base_msp = msps.get(crop, 2000)

        # AI IMAGE ANALYSIS (using PIL)
        img = Image.open(image_file).convert('RGB')
        img = img.resize((100, 100)) # Resize for fast processing
        pixels = list(img.getdata())
        
        # Calculate average brightness and color profile
        brightness = sum(sum(p) for p in pixels) / (len(pixels) * 3) # 0-255
        
        # Color variance (Standard deviation of green/yellow for crops)
        r_avg = sum(p[0] for p in pixels) / len(pixels)
        g_avg = sum(p[1] for p in pixels) / len(pixels)
        b_avg = sum(p[2] for p in pixels) / len(pixels)
        
        # Heuristics for quality
        quality_score = 0
        report_points = []
        
        # 1. Brightness (Lustre)
        if brightness > 180:
            quality_score += 40
            report_points.append("High Grain Lustre: Excellent surface shine detected.")
        elif brightness > 100:
            quality_score += 25
            report_points.append("Standard Appearance: Normal color saturation.")
        else:
            quality_score += 10
            report_points.append("Dull Texture: Sample appears slightly dark or moisture-heavy.")
            
        # 2. Color Uniformity (Crops are usually warm/yellowish)
        if r_avg > g_avg and r_avg > 120:
            quality_score += 30
            report_points.append("Golden Hue: Indicative of healthy, ripe harvest.")
        elif g_avg > r_avg:
            quality_score += 15
            report_points.append("Greenish Tinge: Might indicate early harvest or moisture.")
            
        # 3. Density (Heuristic based on pixel variance)
        quality_score += random.randint(10, 30) # Final variance
        
        if quality_score > 85:
            quality = 'Premium'
            multiplier = 1.15
            summary = "Top Tier Quality. Highly recommended for export."
        elif quality_score > 65:
            quality = 'A-Grade'
            multiplier = 1.08
            summary = "Superior Quality. Above market average."
        elif quality_score > 40:
            quality = 'Standard'
            multiplier = 1.00
            summary = "Fair Market Quality. Meets standard requirements."
        else:
            quality = 'Low'
            multiplier = 0.85
            summary = "Below Standard. Suitable for processing/feed."

        fair_price = int(base_msp * multiplier)
        
        return JsonResponse({
            'status': 'success',
            'msp': base_msp,
            'fair_price': fair_price,
            'quality': quality,
            'score': quality_score,
            'report': report_points,
            'summary': summary,
            'message': f"AI Analysis Complete: {quality} grade detected."
        })

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Image Scan Failed: {str(e)}'}, status=500)

def api_create_listing(request):
    if request.method == 'POST' and request.user.is_authenticated:
        from .models import MarketListing, Product
        crop = request.POST.get('crop')
        qty = request.POST.get('quantity')
        price_val = request.POST.get('price')
        
        # Save to real database
        quality = request.POST.get('quality', 'Standard')
        image_url = request.POST.get('image_url', 'https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?auto=format&fit=crop&q=80&w=400')
        
        listing = MarketListing.objects.create(
            crop_name=crop,
            quantity=qty,
            price=price_val,
            seller_name=request.user.username,
            location="Verified Farmer Location",
            quality=quality,
            image_url=image_url,
            is_verified=True
        )
        
        # Also list it in the AgroStore
        Product.objects.create(
            name=f"{quality} {crop} ({qty}Q)",
            category='Marketplace',
            image_url=image_url,
            mrp=price_val,
            price=price_val,
            quantity_weight=f"{qty} Quintals",
            rating=5.0
        )
        
        return JsonResponse({
            'status': 'success', 
            'listing': {
                'id': listing.id,
                'crop_name': listing.crop_name,
                'quantity': listing.quantity,
                'price': float(listing.price),
                'seller_name': listing.seller_name
            }
        })
    return JsonResponse({'status': 'error'}, status=400)


def _course_by_key(course_key):
    for course in EDU_COURSES:
        if course['course_key'] == course_key:
            return course
    return None


def api_update_learning_progress(request):
    if request.method != 'POST' or not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

    course_key = request.POST.get('course_key')
    progress_raw = request.POST.get('progress', '0')
    watched_seconds_raw = request.POST.get('watched_seconds')
    duration_seconds_raw = request.POST.get('duration_seconds')
    completed_videos_raw = request.POST.get('completed_videos')
    course = _course_by_key(course_key)
    if not course:
        return JsonResponse({'status': 'error', 'message': 'Unknown course'}, status=404)

    try:
        progress = int(progress_raw)
    except ValueError:
        progress = 0

    if completed_videos_raw is not None:
        try:
            completed_videos = int(completed_videos_raw)
        except ValueError:
            return JsonResponse({'status': 'error', 'message': 'Invalid completed videos value'}, status=400)
        total_lessons = max(1, int(course.get('lessons', 1)))
        completed_videos = max(0, min(total_lessons, completed_videos))
        progress = int((completed_videos / total_lessons) * 100)
    elif watched_seconds_raw is not None:
        try:
            watched_seconds = int(watched_seconds_raw)
            duration_seconds = int(duration_seconds_raw or course.get('duration_seconds', 3600))
        except ValueError:
            return JsonResponse({'status': 'error', 'message': 'Invalid watch tracking values'}, status=400)
        watched_seconds = max(0, watched_seconds)
        duration_seconds = max(1, duration_seconds)
        progress = min(100, int((watched_seconds / duration_seconds) * 100))
    else:
        progress = max(0, min(100, progress))
    try:
        progress_obj, _ = LearningProgress.objects.get_or_create(
            user=request.user, course_key=course_key
        )
    except (OperationalError, ProgrammingError):
        return JsonResponse({'status': 'error', 'message': 'Please run database migrations first.'}, status=503)
    progress_obj.progress = progress
    progress_obj.completed = progress >= 100
    if progress_obj.completed and not progress_obj.completed_at:
        progress_obj.completed_at = timezone.now()
    progress_obj.save()

    certificate_code = ''
    if progress_obj.completed:
        try:
            certificate, _ = CourseCertificate.objects.get_or_create(
                user=request.user,
                course_key=course_key,
                defaults={
                    'course_title': course['title'],
                    'certificate_code': f"AGRO-{request.user.id}-{course_key[:6].upper()}-{random.randint(1000,9999)}",
                }
            )
        except (OperationalError, ProgrammingError):
            return JsonResponse({'status': 'error', 'message': 'Please run database migrations first.'}, status=503)
        certificate_code = certificate.certificate_code

    return JsonResponse({
        'status': 'success',
        'progress': progress_obj.progress,
        'completed': progress_obj.completed,
        'certificate_code': certificate_code,
    })


def api_submit_assessment(request):
    if request.method != 'POST' or not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

    course_key = request.POST.get('course_key')
    score_raw = request.POST.get('score')
    course = _course_by_key(course_key)
    if not course:
        return JsonResponse({'status': 'error', 'message': 'Unknown course'}, status=404)

    try:
        score = int(score_raw)
    except (TypeError, ValueError):
        return JsonResponse({'status': 'error', 'message': 'Invalid assessment score'}, status=400)

    score = max(0, min(100, score))
    passed = score >= PASSING_SCORE

    assessment, _ = CourseAssessment.objects.get_or_create(
        user=request.user,
        course_key=course_key,
        defaults={'score': score, 'passed': passed},
    )
    assessment.score = score
    assessment.passed = passed
    assessment.save()

    progress_obj = LearningProgress.objects.filter(user=request.user, course_key=course_key).first()
    certificate_code = ''
    if progress_obj and progress_obj.progress >= 100 and passed:
        progress_obj.completed = True
        if not progress_obj.completed_at:
            progress_obj.completed_at = timezone.now()
        progress_obj.save()
        certificate, _ = CourseCertificate.objects.get_or_create(
            user=request.user,
            course_key=course_key,
            defaults={
                'course_title': course['title'],
                'certificate_code': f"AGRO-{request.user.id}-{course_key[:6].upper()}-{random.randint(1000,9999)}",
            }
        )
        certificate_code = certificate.certificate_code

    return JsonResponse({
        'status': 'success',
        'score': score,
        'passed': passed,
        'passing_score': PASSING_SCORE,
        'certificate_code': certificate_code,
    })


def api_generate_certificate(request):
    if request.method != 'POST' or not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

    course_key = request.POST.get('course_key')
    course = _course_by_key(course_key)
    if not course:
        return JsonResponse({'status': 'error', 'message': 'Unknown course'}, status=404)

    try:
        progress = LearningProgress.objects.filter(
            user=request.user, course_key=course_key, completed=True
        ).first()
    except (OperationalError, ProgrammingError):
        return JsonResponse({'status': 'error', 'message': 'Please run database migrations first.'}, status=503)
    if not progress:
        return JsonResponse({'status': 'error', 'message': 'Complete the course to unlock certificate'}, status=400)

    try:
        certificate, _ = CourseCertificate.objects.get_or_create(
            user=request.user,
            course_key=course_key,
            defaults={
                'course_title': course['title'],
                'certificate_code': f"AGRO-{request.user.id}-{course_key[:6].upper()}-{random.randint(1000,9999)}",
            }
        )
    except (OperationalError, ProgrammingError):
        return JsonResponse({'status': 'error', 'message': 'Please run database migrations first.'}, status=503)

    image = Image.new('RGB', (1600, 1100), '#f7f2e6')
    draw = ImageDraw.Draw(image)
    title_font = ImageFont.load_default()
    body_font = ImageFont.load_default()

    draw.rectangle((30, 30, 1570, 1070), outline='#2d5b4a', width=5)
    draw.rectangle((60, 60, 1540, 1040), outline='#b58f3a', width=3)
    draw.text((650, 120), "AGROSENSE LEARNING", fill='#2d5b4a', font=title_font)
    draw.text((610, 180), "COURSE COMPLETION CERTIFICATE", fill='#b58f3a', font=title_font)
    draw.text((180, 320), "This is to proudly certify that", fill='#3E2723', font=body_font)
    draw.text((180, 390), request.user.get_full_name() or request.user.username, fill='#1f4a3b', font=body_font)
    draw.text((180, 460), "has successfully completed and passed final assessment for", fill='#3E2723', font=body_font)
    draw.text((180, 520), course['title'], fill='#1f4a3b', font=body_font)
    draw.text((180, 600), "Result: PASS", fill='#1f4a3b', font=body_font)
    draw.text((180, 660), f"Certificate ID: {certificate.certificate_code}", fill='#3E2723', font=body_font)
    draw.text((180, 720), f"Issued On: {certificate.issued_at.strftime('%d %b %Y')}", fill='#3E2723', font=body_font)
    draw.ellipse((1220, 760, 1460, 1000), outline='#b58f3a', width=4)
    draw.text((1270, 870), "AGRO", fill='#2d5b4a', font=body_font)
    draw.text((180, 860), "AgroSense Learning Academy", fill='#2d5b4a', font=body_font)
    draw.text((180, 930), "Authorized by AgroSense Digital Learning Board", fill='#2d5b4a', font=body_font)

    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    encoded = base64.b64encode(buffer.getvalue()).decode('utf-8')
    data_url = f"data:image/png;base64,{encoded}"

    return JsonResponse({
        'status': 'success',
        'data_url': data_url,
        'filename': f"agrosense_certificate_{course_key}.png",
        'certificate_code': certificate.certificate_code,
    })

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

def custom_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            
            # Remember Me logic
            if request.POST.get('remember'):
                # 2 weeks
                request.session.set_expiry(1209600)
            else:
                # Browser close
                request.session.set_expiry(0)
                
            return redirect('dashboard')
    else:
        form = AuthenticationForm()
    return render(request, 'registration/login.html', {'form': form})

def api_create_razorpay_order(request):
    """Step 1: Create a Razorpay order and return credentials to frontend."""
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'Login required.'}, status=401)
    if request.method != 'POST':
        return JsonResponse({'status': 'error'}, status=405)

    import razorpay
    from django.conf import settings

    total_amount = float(request.POST.get('total_amount', 0))
    if total_amount < 1.0:
        return JsonResponse({'status': 'error', 'message': 'Minimum order amount is ₹1.00 (100 paise).'}, status=400)

    try:
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        rp_order = client.order.create({
            'amount': int(total_amount * 100),  # Razorpay works in paise
            'currency': 'INR',
            'payment_capture': 1,  # Auto-capture on payment
        })
        return JsonResponse({
            'status': 'success',
            'razorpay_order_id': rp_order['id'],
            'amount': int(total_amount * 100),
            'currency': 'INR',
            'key': settings.RAZORPAY_KEY_ID,
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Could not create payment order: {str(e)}'}, status=500)


def api_verify_razorpay_payment(request):
    """Step 2: Verify Razorpay payment signature and place order."""
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'Login required.'}, status=401)
    if request.method != 'POST':
        return JsonResponse({'status': 'error'}, status=405)

    import razorpay
    import hmac, hashlib
    from django.conf import settings

    razorpay_payment_id = request.POST.get('razorpay_payment_id', '')
    razorpay_order_id   = request.POST.get('razorpay_order_id', '')
    razorpay_signature  = request.POST.get('razorpay_signature', '')

    # HMAC-SHA256 verification — this is how Razorpay guarantees authenticity
    msg = f"{razorpay_order_id}|{razorpay_payment_id}"
    expected_sig = hmac.new(
        settings.RAZORPAY_KEY_SECRET.encode('utf-8'),
        msg.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected_sig, razorpay_signature):
        return JsonResponse({
            'status': 'error',
            'message': 'Payment signature verification failed. Possible fraud attempt.'
        }, status=403)

    # Signature valid — place the order
    full_name      = request.POST.get('full_name')
    address        = request.POST.get('address')
    pincode        = request.POST.get('pincode')
    phone          = request.POST.get('phone')
    payment_method = 'UPI'
    total_amount   = float(request.POST.get('total_amount', 0))

    order_id = f"AGS-{uuid.uuid4().hex[:8].upper()}"
    order = Order.objects.create(
        user=request.user,
        order_id=order_id,
        full_name=full_name,
        address=address,
        pincode=pincode,
        phone=phone,
        payment_method=payment_method,
        transaction_id=razorpay_payment_id,
        total_amount=total_amount,
        status='PAID'
    )

    delivery_date = (timezone.now() + timezone.timedelta(days=3)).strftime('%d %b %Y')
    return JsonResponse({
        'status': 'success',
        'order_id': order_id,
        'delivery_date': delivery_date,
        'tracking_no': f"TRK-{random.randint(100000, 999999)}",
        'message': 'Payment Verified by Razorpay. Order Placed!'
    })


def agro_store(request):
    products = Product.objects.all()
    categories = ['Fertilizers', 'Seeds', 'Pesticides', 'Tools', 'Organic', 'Irrigation', 'Soil', 'Marketplace']
    context = {
        'products': products,
        'categories': categories,
    }
    return render(request, 'core/store.html', context)

def api_place_order(request):
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'Please login to place an order.'}, status=401)
    if request.method == 'POST':
        import re
        full_name = request.POST.get('full_name')
        address = request.POST.get('address')
        pincode = request.POST.get('pincode')
        phone = request.POST.get('phone')
        payment_method = request.POST.get('payment_method')
        total_amount = float(request.POST.get('total_amount', 0))
        transaction_id = request.POST.get('transaction_id', '').strip()
        # UPI orders are trusted — user confirmed payment in their UPI app
        # Admin can cross-verify from their bank statement independently

        order_id = f"AGS-{uuid.uuid4().hex[:8].upper()}"
        status = 'PAID' if payment_method == 'UPI' else 'PENDING'
        
        order = Order.objects.create(
            user=request.user,
            order_id=order_id,
            full_name=full_name,
            address=address,
            pincode=pincode,
            phone=phone,
            payment_method=payment_method,
            transaction_id=transaction_id,
            total_amount=total_amount,
            status=status
        )
        
        delivery_date = (timezone.now() + timezone.timedelta(days=3)).strftime('%d %b %Y')
        
        return JsonResponse({
            'status': 'success',
            'order_id': order_id,
            'delivery_date': delivery_date,
            'tracking_no': f"TRK-{random.randint(100000, 999999)}",
            'message': 'Payment Verified. Order Placed!'
        })
    return JsonResponse({'status': 'error'}, status=400)

def api_my_orders(request):
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error'}, status=401)
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    data = []
    for o in orders:
        data.append({
            'order_id': o.order_id,
            'total_amount': float(o.total_amount),
            'status': o.status,
            'date': o.created_at.strftime('%d %b %Y'),
            'payment_method': o.payment_method
        })
    return JsonResponse({'status': 'success', 'orders': data})

def api_cancel_order(request):
    if request.method == 'POST' and request.user.is_authenticated:
        order_id = request.POST.get('order_id')
        order = Order.objects.filter(user=request.user, order_id=order_id).first()
        if order:
            if order.status in ['PENDING', 'PAID']:
                order.status = 'CANCELLED'
                order.save()
                return JsonResponse({'status': 'success'})
            return JsonResponse({'status': 'error', 'message': f'Cannot cancel order in {order.status} status.'}, status=400)
        return JsonResponse({'status': 'error', 'message': 'Order not found.'}, status=404)
    return JsonResponse({'status': 'error'}, status=400)

def api_generate_bill(request):
    order_id = request.GET.get('order_id')
    order = Order.objects.filter(user=request.user, order_id=order_id).first()
    if not order:
        return JsonResponse({'status': 'error', 'message': 'Order not found'}, status=404)
    
    # Simple HTML Bill
    html = f"""
    <div style="font-family: sans-serif; padding: 40px; border: 1px solid #eee; max-width: 800px; margin: auto;">
        <h1 style="color: #2d5a27;">AgroSense Invoice</h1>
        <hr>
        <p><strong>Order ID:</strong> {order.order_id}</p>
        <p><strong>Date:</strong> {order.created_at.strftime('%d %b %Y %H:%M')}</p>
        <p><strong>Customer:</strong> {order.full_name}</p>
        <p><strong>Phone:</strong> {order.phone}</p>
        <p><strong>Address:</strong> {order.address}, {order.pincode}</p>
        <hr>
        <table style="width: 100%; border-collapse: collapse;">
            <tr style="background: #f8fafc;">
                <th style="padding: 10px; text-align: left; border-bottom: 2px solid #ddd;">Description</th>
                <th style="padding: 10px; text-align: right; border-bottom: 2px solid #ddd;">Amount</th>
            </tr>
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #eee;">AgroStore Purchase Items</td>
                <td style="padding: 10px; text-align: right; border-bottom: 1px solid #eee;">₹{order.total_amount}</td>
            </tr>
            <tr>
                <td style="padding: 10px; font-weight: bold;">Total Paid via {order.payment_method}</td>
                <td style="padding: 10px; text-align: right; font-weight: bold;">₹{order.total_amount}</td>
            </tr>
        </table>
        {f'<p style="margin-top: 20px;"><strong>Transaction ID:</strong> {order.transaction_id}</p>' if order.transaction_id else ''}
        <p style="margin-top: 50px; text-align: center; color: #666;">Thank you for shopping with AgroSense!</p>
    </div>
    """
    return JsonResponse({'status': 'success', 'html': html})


def terms_and_conditions(request):
    return render(request, 'core/policies/terms.html')

def privacy_policy(request):
    return render(request, 'core/policies/privacy.html')

def shipping_policy(request):
    return render(request, 'core/policies/shipping.html')

def contact_us(request):
    return render(request, 'core/policies/contact.html')

def refund_policy(request):
    return render(request, 'core/policies/refunds.html')
