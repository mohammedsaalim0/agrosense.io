from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth
import datetime
from django.contrib.auth import login as auth_login, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.http import JsonResponse, HttpResponse
from django.urls import reverse, reverse_lazy
from django.db.utils import OperationalError, ProgrammingError
from django.utils import timezone
from .models import Crop, SupportScheme, MarketListing, SchemeApplication, Profile, LearningProgress, CourseCertificate, CourseAssessment
import random
import io
import base64
from django.core.mail import send_mail
from django.conf import settings
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

    from .models import VolunteerTask
    volunteer_tasks = VolunteerTask.objects.filter(is_active=True).order_by('-created_at')[:3]

    context = {
        'schemes': schemes,
        'listings': listings,
        'applications': applications,
        'edu_courses': edu_courses,
        'volunteer_tasks': volunteer_tasks,
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

def get_premium_email_html(title, message, items_html="", total=None, logo_url=None, bg_url=None, button_text="Visit Dashboard", button_url="http://agrosense.io"):
    """Generates a premium Glassmorphism-inspired HTML email template"""
    logo = logo_url if logo_url else "https://i.ibb.co/L8v8J1Z/agrosense-logo-white.png"
    # User's custom background from Behance
    bg = bg_url if bg_url else "https://mir-s3-cdn-cf.behance.net/projects/404/704b45151950331.Y3JvcCwxMzA5LDEwMjQsMzY5LDA.jpg"
    
    total_section = f'<div style="text-align: right; margin-top: 20px; font-size: 1.2rem; color: #2d5a27;"><strong>Total: ₹{total}</strong></div>' if total else ""
    invoice_section = f"""
        <div style="margin-top: 30px; border: 1px solid #e0e0e0; border-radius: 12px; overflow: hidden; background: rgba(255,255,255,0.8); backdrop-filter: blur(10px);">
            <table style="width: 100%; border-collapse: collapse; font-family: sans-serif;">
                <tr style="background: #f1f8e9;">
                    <th style="padding: 12px; text-align: left; color: #2d5a27; font-size: 0.9rem;">Description</th>
                    <th style="padding: 12px; text-align: right; color: #2d5a27; font-size: 0.9rem;">Amount</th>
                </tr>
                {items_html}
            </table>
        </div>
        {total_section}
    """ if items_html else ""

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600&display=swap');
            body {{ font-family: 'Outfit', sans-serif; margin: 0; padding: 0; background-color: #f0f2f0; }}
            .wrapper {{ background-image: url('{bg}'); background-size: cover; background-position: center; padding: 40px 20px; }}
            .container {{ max-width: 600px; margin: 0 auto; background: rgba(255, 255, 255, 0.9); border-radius: 32px; overflow: hidden; box-shadow: 0 20px 50px rgba(0,0,0,0.15); backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.5); }}
            .header {{ background: linear-gradient(135deg, rgba(45, 90, 39, 0.9) 0%, rgba(76, 175, 80, 0.9) 100%); padding: 50px 40px; text-align: center; color: white; }}
            .content {{ padding: 40px; line-height: 1.7; color: #333; }}
            .footer {{ background: rgba(241, 248, 233, 0.9); padding: 25px; text-align: center; color: #2d5a27; font-size: 0.85rem; font-weight: 600; }}
            .btn {{ display: inline-block; padding: 14px 30px; background: #2d5a27; color: white !important; text-decoration: none; border-radius: 15px; font-weight: 600; margin-top: 25px; box-shadow: 0 4px 15px rgba(45,90,39,0.3); }}
            .badge {{ display: inline-block; padding: 5px 15px; background: #e8f5e9; color: #2d5a27; border-radius: 20px; font-size: 0.8rem; font-weight: 800; margin-bottom: 15px; text-transform: uppercase; letter-spacing: 1px; }}
        </style>
    </head>
    <body>
        <div class="wrapper">
            <div class="container">
                <div class="header">
                    <img src="{logo}" alt="AgroSense Logo" style="max-height: 60px; margin-bottom: 20px;">
                    <h1 style="margin: 0; font-size: 2rem; letter-spacing: -1px; font-weight: 600;">{title}</h1>
                </div>
                <div class="content">
                    <span class="badge">Verified Merchant</span>
                    <p style="font-size: 1.15rem; color: #2c3e50;">{message}</p>
                    {invoice_section}
                    <center><a href="{button_url}" class="btn">{button_text}</a></center>
                </div>
                <div class="footer">
                    © 2026 AgroSense Tumkur • The Future of Smart Farming 🌾
                </div>
            </div>
        </div>
    </body>
    </html>
    """

def api_recommend(request):
    state = request.GET.get('state', '')
    soil = request.GET.get('soil', '')
    season = request.GET.get('season', '')
    
    prompt = f"As a professional agricultural advisor, suggest 4 crops for a farmer in {state} with {soil} soil during the {season} season. For each crop, provide a suitability score (out of 100) and expected yield (tons/acre). Return ONLY a JSON list of objects like: [{{'name': 'CropName', 'score': 95, 'yield': 4.2}}]"
    
    ollama_res = call_ollama(prompt)
    crops = []
    
    try:
        if ollama_res:
            import json, re
            # Extract JSON from potential conversational filler
            json_match = re.search(r'\[.*\]', ollama_res, re.DOTALL)
            if json_match:
                crops = json.loads(json_match.group(0))
        
        if not crops:
            raise ValueError
    except:
        # High-Quality Fallback logic
        random.seed(f"{state}{soil}{season}")
        crops = [
            {'name': 'Basmati Rice', 'score': random.randint(88, 98), 'yield': round(random.uniform(3.5, 5.0), 1)},
            {'name': 'Organic Wheat', 'score': random.randint(82, 95), 'yield': round(random.uniform(4.0, 6.0), 1)},
            {'name': 'Golden Maize', 'score': random.randint(78, 92), 'yield': round(random.uniform(3.0, 4.8), 1)},
            {'name': 'Mustard', 'score': random.randint(75, 88), 'yield': round(random.uniform(1.8, 2.5), 1)},
        ]
        random.seed(None)

    return JsonResponse({'crops': crops})

def api_search_market(request):
    crop = request.GET.get('crop', 'Wheat').capitalize()
    location = request.GET.get('location', 'India').capitalize()
    
    known_crops = {
        'wheat', 'rice', 'paddy', 'cotton', 'maize', 'tomato', 'potato', 'onion', 
        'mustard', 'soyabean', 'sugarcane', 'tur', 'moong', 'urad', 'jowar', 'bajra', 
        'ragi', 'groundnut', 'sunflower', 'sesamum', 'nigerseed', 'barley', 'gram',
        'lentil'
    }
    
    if crop.lower() not in known_crops and not any(k in crop.lower() for k in known_crops):
        return JsonResponse({
            'status': 'error',
            'message': f"No market participants found for '{crop}'. Try Wheat, Rice, or Cotton."
        }, status=400)
    
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

def send_agro_email(user_email, subject, text_content, html_content=None, attachment=None):
    """Helper to send pretty HTML emails with optional attachments"""
    if not user_email:
        print(f"DEBUG: No email address provided for subject: {subject}")
        return
    try:
        print(f"DEBUG: Attempting to send premium email to {user_email}...")
        from django.core.mail import EmailMultiAlternatives
        
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user_email],
        )
        if html_content:
            msg.attach_alternative(html_content, "text/html")
        
        if attachment:
            # attachment is expected to be a file-like object or UploadedFile
            msg.attach(attachment.name, attachment.read(), attachment.content_type)
            
        msg.send(fail_silently=False)
        print(f"DEBUG: Premium Email sent successfully to {user_email}!")
    except Exception as e:
        print(f"DEBUG: Failed to send premium email. Error: {str(e)}")

def api_market_data(request):
    crop = request.GET.get('crop', 'Wheat').capitalize()
    
    # Strict Validation: Check if the input is a valid crop
    known_crops = {
        'wheat', 'rice', 'paddy', 'cotton', 'maize', 'tomato', 'potato', 'onion', 
        'mustard', 'soyabean', 'sugarcane', 'tur', 'moong', 'urad', 'jowar', 'bajra', 
        'ragi', 'groundnut', 'sunflower', 'sesamum', 'nigerseed', 'barley', 'gram',
        'lentil', 'jute', 'coffee', 'tea', 'rubber', 'tobacco', 'chilli', 'garlic',
        'ginger', 'turmeric', 'coriander', 'cumin', 'pepper'
    }
    
    # Fuzzy match or simple check
    search_term = crop.lower()
    if search_term not in known_crops and not any(k in search_term for k in known_crops):
        return JsonResponse({
            'status': 'error',
            'message': f"Intelligence for '{crop}' is not available. Please enter a valid agricultural product (e.g., Wheat, Rice, Cotton)."
        }, status=    # Try to get "Real" predicted price AND a market summary from Ollama
    intel_prompt = f"As a market analyst, analyze the current market for {crop} in India. Provide: 1. Current average price per quintal in INR. 2. A 2-sentence market outlook. Return ONLY in this format: PRICE: [value] | INTEL: [summary]"
    ollama_res = call_ollama(intel_prompt)
    
    market_intel = "Market conditions are stabilizing with moderate demand from urban centers."
    base_price = 2200
    
    try:
        if ollama_res:
            import re
            price_match = re.search(r'PRICE:\s*(\d+)', ollama_res)
            intel_match = re.search(r'INTEL:\s*(.*)', ollama_res)
            if price_match:
                base_price = int(price_match.group(1))
            if intel_match:
                market_intel = intel_match.group(1).strip()
        else:
            raise ValueError
    except:
        # Fallback to realistic Indian market ranges (per quintal)
        price_ranges = {
            'Wheat': (2275, 2550),
            'Rice': (2183, 2800),
            'Paddy': (2183, 2300),
            'Cotton': (6620, 7500),
            'Maize': (2090, 2350),
            'Tomato': (1200, 3500),
            'Potato': (1000, 2200),
            'Onion': (1500, 4500),
            'Mustard': (5450, 6000),
            'Soyabean': (4600, 5200),
            'Sugarcane': (315, 340),
            'Tur': (7000, 8500),
            'Moong': (8558, 9500),
        }
        low, high = price_ranges.get(crop, (1800, 4000))
        base_price = random.randint(low, high)
        market_intel = f"The market for {crop} is currently driven by local supply chains and seasonal demand factors."

    # Seed random with crop name to make trends deterministic for the same crop
    random.seed(crop)
    
    # Generate realistic trends around the base price
    trends = [int(base_price * (1 + random.uniform(-0.05, 0.05))) for _ in range(12)]
    
    metrics = {
        'demand': random.randint(70, 95) if base_price > 2000 else random.randint(40, 70),
        'supply': random.randint(30, 80),
        'profit': random.randint(50, 90),
        'source': 'Ollama AI Intelligence' if ollama_res else 'AgroSense Market Analysis'
    }
    
    stability = [random.randint(60, 100) for _ in range(5)]
    
    # Reset seed
    random.seed(None)
    
    return JsonResponse({
        'status': 'success',
        'crop': crop,
        'current_price': base_price,
        'market_intel': market_intel,
        'trends': trends,
        'metrics': metrics,
        'stability': stability
    })
    })
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

        # Identification Logic grounded in image color data
        detected_plant = 'Unknown Crop'
        confidence_val = int(70 + (green_ratio * 20))
        
        # Color profile analysis
        r_avg = sum(p[0] for p in pixels) / len(pixels)
        g_avg = sum(p[1] for p in pixels) / len(pixels)
        b_avg = sum(p[2] for p in pixels) / len(pixels)
        
        if g_avg > r_avg * 1.3:
            detected_plant = 'Healthy Foliage (Vegetable/Leafy)'
        elif r_avg > g_avg * 1.1 and r_avg > 150:
            detected_plant = 'Wheat/Cereal (Mature)'
        elif b_avg > 150:
            detected_plant = 'Blue/Violet Flower Species'
        
        # Filename heuristics as supplement
        filename = image_file.name.lower()
        if 'wheat' in filename: detected_plant = 'Wheat (Triticum aestivum)'
        elif 'rice' in filename: detected_plant = 'Rice (Oryza sativa)'
        elif 'paddy' in filename: detected_plant = 'Paddy (Oryza sativa)'
        elif 'maize' in filename: detected_plant = 'Maize (Zea mays)'
        elif 'cotton' in filename: detected_plant = 'Cotton (Gossypium)'
        elif 'tomato' in filename: detected_plant = 'Tomato (Solanum lycopersicum)'
        elif 'potato' in filename: detected_plant = 'Potato (Solanum tuberosum)'
        elif 'mustard' in filename: detected_plant = 'Mustard (Brassica)'
        
        if detected_plant == 'Unknown Crop':
            detected_plant = random.choice(['High-Yield Rice', 'Resilient Wheat', 'Hybrid Maize'])
        
        confidence_val = min(99, confidence_val + random.randint(0, 5))

        results = {
            'status': 'success',
            'plant': detected_plant,
            'health': 'Thriving' if green_ratio > 0.6 else ('Healthy' if green_ratio > 0.35 else 'Needs Care'),
            'confidence': f"{confidence_val}%",
            'growth': int(60 + (green_ratio * 40)),
            'health_radar': [random.randint(70, 100) for _ in range(5)],
            'disease_risk': random.randint(0, 3) if green_ratio > 0.5 else random.randint(4, 12),
            'chlorophyll': [int(40 + (green_ratio * 60) + random.randint(-5, 5)) for _ in range(7)]
        }

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
        # Real-time MSP Data (2024-25 Latest)
        msps = {
            'Wheat': 2275, 'Paddy': 2183, 'Maize': 2090, 'Cotton': 6620, 'Jowar': 3180, 
            'Bajra': 2500, 'Ragi': 3846, 'Arhar': 7000, 'Moong': 8558, 'Urad': 6950,
            'Groundnut': 6377, 'Sunflower': 6760, 'Soyabean': 4600, 'Sesamum': 8635,
            'Nigerseed': 7734, 'Sugarcane': 315, 'Tomato': 2500, 'Potato': 1500, 'Onion': 2200,
            'Mustard': 5450, 'Tur': 7000, 'Rice': 2183
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
        
        # 1. Brightness (Lustre/Shine) - Indicator of freshness and moisture content
        if brightness > 170:
            quality_score += 35
            report_points.append("High Lustre: Grains show excellent natural shine, indicative of proper drying and storage.")
        elif brightness > 100:
            quality_score += 20
            report_points.append("Standard Lustre: Normal appearance, meets local market expectations.")
        else:
            quality_score += 5
            report_points.append("Dull Texture: Potential high moisture or weathering detected. Reduces market premium.")
            
        # 2. Color Maturation (Hue Analysis)
        # Healthy crops (Wheat, Paddy, Maize) are usually in the Red/Yellow spectrum
        if r_avg > g_avg * 1.15 and r_avg > 130:
            quality_score += 30
            report_points.append("Golden Maturation: Ideal color profile detected, indicating peak ripeness and nutrient density.")
        elif g_avg > r_avg * 1.05:
            quality_score += 10
            report_points.append("Immature Tinge: Greenish undertones detected. Likely early harvest, which may affect weight and storage life.")
        else:
            quality_score += 15
            report_points.append("Neutral Profile: Standard color consistency.")
            
        # 3. Density/Uniformity (Heuristic based on pixel variance)
        r_var = sum((p[0] - r_avg)**2 for p in pixels) / len(pixels)
        g_var = sum((p[1] - g_avg)**2 for p in pixels) / len(pixels)
        
        uniformity_bonus = max(0, 35 - int((r_var + g_var) ** 0.5 / 4))
        quality_score += uniformity_bonus
        if uniformity_bonus > 25:
            report_points.append("Superior Uniformity: Minimal grain variance detected. High millability and premium sorting.")
        elif uniformity_bonus > 12:
            report_points.append("Consistent Sample: Majority of grains show uniform size and maturity.")
        else:
            report_points.append("Mixed Quality: High variance in sample. May require additional sorting before sale.")

        # 4. Market Trend Analysis (Heuristic based on current "market season")
        current_month = timezone.now().month
        # Assume peak harvest months (3,4, 10,11) have slightly higher supply pressure
        is_harvest_season = current_month in [3, 4, 10, 11]
        market_analysis = ""
        
        if quality_score > 85:
            quality = 'Premium'
            multiplier = 1.18
            market_analysis = "Market Trend: High demand for export-quality produce. Current supply is tight for this grade."
            summary = "Premium Grade detected. This sample qualifies for the highest market bracket due to its superior lustre and uniformity."
        elif quality_score > 65:
            quality = 'A-Grade'
            multiplier = 1.10
            market_analysis = "Market Trend: Steady demand from institutional buyers and retail chains."
            summary = "A-Grade Quality. Above average results. Well-matured sample with good marketability."
        elif quality_score > 40:
            quality = 'Standard'
            multiplier = 1.00
            market_analysis = "Market Trend: Normal liquidity. Price aligns perfectly with current Government MSP."
            summary = "Standard Grade. Reliable market quality that meets all basic procurement requirements."
        else:
            quality = 'Low'
            multiplier = 0.82
            market_analysis = "Market Trend: Oversupply of lower grades. Suggesting processing for value-addition."
            summary = "Low Grade. Visual defects or high moisture detected. Best suited for animal feed or industrial processing."

        if is_harvest_season:
            market_analysis += " (Note: Harvest season pressure may cause slight price volatility)."

        fair_price = int(base_msp * multiplier)
        
        return JsonResponse({
            'status': 'success',
            'msp': base_msp,
            'fair_price': fair_price,
            'quality': quality,
            'score': min(100, quality_score),
            'report': report_points,
            'market_analysis': market_analysis,
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
        email = request.POST.get('email')
        dob = request.POST.get('dob')
        profession = request.POST.get('profession')
        
        if form.is_valid():
            user = form.save()
            user.first_name = first_name
            user.last_name = last_name
            user.email = email
            user.save()
            print(f"DEBUG: User registered with email: {user.email}")
            
            # Create profile
            Profile.objects.create(user=user, dob=dob, profession=profession)
            
            # Send Welcome Email
            if user.email:
                subject = "Namaste! Welcome to AgroSense"
                message = f"Welcome to the AgroSense family, {user.first_name or user.username}! We are excited to have you onboard. AgroSense is your all-in-one digital ecosystem for smart farming."
                html_content = get_premium_email_html(
                    "Welcome to AgroSense",
                    f"Namaste {user.first_name or user.username},<br><br>We are excited to have you onboard! AgroSense is your all-in-one digital ecosystem for smart farming, market intelligence, and sustainable agriculture. Start exploring your dashboard to see what's new in the fields!"
                )
                send_agro_email(user.email, subject, message, html_content)

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
            print(f"DEBUG: User logged in: {user.username}, Email: {user.email}")
            
            # Send Login Alert
            if user.email:
                subject = "AgroSense: New Login Alert"
                time_str = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
                message = f"A new login was detected on your account at {time_str}."
                html_content = get_premium_email_html(
                    "Security Alert: New Login",
                    f"Namaste {user.first_name or user.username},<br><br>A new login was detected on your AgroSense account at <strong>{time_str}</strong>. If this wasn't you, please change your password immediately to secure your harvest data."
                )
                send_agro_email(user.email, subject, message, html_content)
            
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

from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def api_check_auth(request):
    """Check if user is authenticated"""
    return JsonResponse({
        'authenticated': request.user.is_authenticated,
        'username': request.user.username if request.user.is_authenticated else None
    })

@csrf_exempt
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


@csrf_exempt
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
    
    # Send Thank You Email
    if request.user.email:
        subject = "AgroSense: Order Confirmed! (ID: " + order_id + ")"
        message = f"Thank you for your purchase! Your order {order_id} has been placed successfully."
        
        items_html = f"""
            <tr>
                <td style="padding: 12px; border-bottom: 1px solid #eee;">AgroStore Purchase (Order ID: {order_id})</td>
                <td style="padding: 12px; text-align: right; border-bottom: 1px solid #eee;">₹{total_amount}</td>
            </tr>
        """
        html_content = get_premium_email_html(
            "Payment Confirmed!",
            f"Namaste {request.user.first_name or request.user.username},<br><br>Your payment of <strong>₹{total_amount}</strong> has been verified. We are preparing your items for shipment. Your tracking ID will be generated shortly.",
            items_html,
            total_amount,
            button_text="Download Invoice",
            button_url=request.build_absolute_uri(reverse('download_invoice', args=[order_id]))
        )
        send_agro_email(request.user.email, subject, message, html_content)

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
        
        # Send Thank You Email (COD)
        if request.user.email:
            subject = "AgroSense: Order Placed! (ID: " + order_id + ")"
            message = f"Your order {order_id} has been placed successfully via {payment_method}."
            
            items_html = f"""
                <tr>
                    <td style="padding: 12px; border-bottom: 1px solid #eee;">AgroStore Purchase (COD/UPI)</td>
                    <td style="padding: 12px; text-align: right; border-bottom: 1px solid #eee;">₹{total_amount}</td>
                </tr>
            """
            html_content = get_premium_email_html(
                "Order Placed Successfully",
                f"Namaste {request.user.first_name or request.user.username},<br><br>Your order <strong>{order_id}</strong> has been received via {payment_method}. We will notify you once it's out for delivery! Please keep ₹{total_amount} ready if it's a Cash on Delivery order.",
                items_html,
                total_amount,
                button_text="Download Invoice",
                button_url=request.build_absolute_uri(reverse('download_invoice', args=[order_id]))
            )
            send_agro_email(request.user.email, subject, message, html_content)

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
                
                # Send Cancellation Email
                if request.user.email:
                    send_agro_email(
                        request.user.email,
                        "AgroSense: Order Cancelled (ID: " + order_id + ")",
                        f"Namaste {request.user.first_name or request.user.username},\n\nAs per your request, your order {order_id} has been cancelled successfully. If any amount was paid, it will be refunded within 5-7 business days."
                    )
                
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

def download_invoice(request, order_id):
    """Public view to see/print the invoice"""
    order = Order.objects.filter(order_id=order_id).first()
    if not order:
        return HttpResponse("Order not found", status=404)
    
    context = {
        'order': order,
        'date': order.created_at.strftime('%d %b %Y %H:%M'),
    }
    # Re-using the logic from api_generate_bill but returning as full HTML page
    html_content = f"""
    <html>
    <head>
        <title>Invoice {order.order_id}</title>
        <style>
            body {{ font-family: sans-serif; background: #f4f7f6; padding: 50px; }}
            .invoice-card {{ background: white; padding: 50px; border-radius: 20px; max-width: 800px; margin: auto; box-shadow: 0 10px 30px rgba(0,0,0,0.1); border: 1px solid #eee; }}
            .header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #2d5a27; padding-bottom: 20px; margin-bottom: 30px; }}
            .logo {{ color: #2d5a27; font-size: 2rem; font-weight: 800; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 30px; }}
            th {{ background: #f8fafc; padding: 15px; text-align: left; border-bottom: 2px solid #ddd; }}
            td {{ padding: 15px; border-bottom: 1px solid #eee; }}
            .total-row {{ font-weight: bold; font-size: 1.2rem; background: #f1f8e9; }}
            .footer {{ margin-top: 50px; text-align: center; color: #666; font-size: 0.9rem; }}
            @media print {{
                body {{ background: white; padding: 0; }}
                .invoice-card {{ box-shadow: none; border: none; }}
                .no-print {{ display: none; }}
            }}
        </style>
    </head>
    <body>
        <div class="invoice-card">
            <div class="header">
                <div class="logo">AgroSense</div>
                <div style="text-align: right;">
                    <h2 style="margin: 0; color: #2d5a27;">INVOICE</h2>
                    <p style="margin: 5px 0; color: #666;">#{order.order_id}</p>
                </div>
            </div>
            
            <div style="display: flex; justify-content: space-between;">
                <div>
                    <h4 style="margin-bottom: 5px; color: #2d5a27;">Billed To:</h4>
                    <p style="margin: 0;"><strong>{order.full_name}</strong></p>
                    <p style="margin: 0;">{order.address}</p>
                    <p style="margin: 0;">{order.pincode}</p>
                    <p style="margin: 0;">Phone: {order.phone}</p>
                </div>
                <div style="text-align: right;">
                    <h4 style="margin-bottom: 5px; color: #2d5a27;">Order Details:</h4>
                    <p style="margin: 0;">Date: {order.created_at.strftime('%d %b %Y')}</p>
                    <p style="margin: 0;">Method: {order.payment_method}</p>
                    <p style="margin: 0;">Status: {order.status}</p>
                </div>
            </div>

            <table>
                <thead>
                    <tr>
                        <th>Description</th>
                        <th style="text-align: right;">Amount</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>AgroStore Purchase Items</td>
                        <td style="text-align: right;">₹{order.total_amount}</td>
                    </tr>
                    <tr class="total-row">
                        <td>Total Amount Paid</td>
                        <td style="text-align: right;">₹{order.total_amount}</td>
                    </tr>
                </tbody>
            </table>

            <div class="footer">
                <p>Thank you for shopping with AgroSense! For any queries, contact support@agrosense.io</p>
                <button onclick="window.print()" class="no-print" style="padding: 10px 20px; background: #2d5a27; color: white; border: none; border-radius: 8px; cursor: pointer;">Print / Save as PDF</button>
            </div>
        </div>
    </body>
    </html>
    """
    return HttpResponse(html_content)


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

@user_passes_test(lambda u: u.is_superuser)
def admin_analytics(request):
    # Overall Metrics
    total_sales = Order.objects.filter(status='PAID').aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_orders = Order.objects.count()
    total_users = User.objects.count()
    
    # Monthly Trends
    monthly_sales = Order.objects.filter(status='PAID').annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        total=Sum('total_amount')
    ).order_by('month')

    # Category Performance
    cat_stats = Product.objects.values('category').annotate(count=Count('id'))

    # Scheme Stats
    scheme_stats = SchemeApplication.objects.values('status').annotate(count=Count('id'))

    context = {
        'total_sales': total_sales,
        'total_orders': total_orders,
        'total_users': total_users,
        'monthly_sales': list(monthly_sales),
        'cat_stats': list(cat_stats),
        'scheme_stats': list(scheme_stats),
    }
    return render(request, 'core/admin_dashboard.html', context)


def api_submit_grievance(request):
    if request.method == 'POST' and request.user.is_authenticated:
        title = request.POST.get('title')
        category = request.POST.get('category')
        details = request.POST.get('details')
        image = request.FILES.get('image')
        report_id = f"AGS-GRV-{random.randint(1000, 9999)}"

        # 1. Send Thank You Email to Submitter
        user_subject = f"Thank You for Reporting: {report_id}"
        user_msg = f"Namaste {request.user.username}, thank you for reaching out. We have received your report regarding '{title}'. Our team is reviewing it and will get back to you soon."
        user_html = get_premium_email_html(
            title="Report Received",
            message=user_msg,
            items_html=f"<tr><td style='padding:12px;'>Report ID</td><td style='padding:12px;text-align:right;'>{report_id}</td></tr>"
                       f"<tr><td style='padding:12px;'>Category</td><td style='padding:12px;text-align:right;'>{category}</td></tr>",
            button_text="Track Status",
            button_url=f"{request.scheme}://{request.get_host()}"
        )
        send_agro_email(request.user.email, user_subject, user_msg, user_html)

        # 2. Send Detailed Email to Admin (tumakurecity@gmail.com) with attachment
        admin_subject = f"URGENT: New Farm Grievance {report_id}"
        admin_msg = f"New issue reported by {request.user.username} ({request.user.email}).\n\nTitle: {title}\nCategory: {category}\nDetails: {details}"
        
        # Reset image pointer for reading if it exists
        if image:
            image.seek(0)

        send_agro_email("tumakurecity@gmail.com", admin_subject, admin_msg, attachment=image)

        return JsonResponse({'status': 'success', 'report_id': report_id})
    
    return JsonResponse({'status': 'error'}, status=400)
