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
                'id': listing.id,
                'crop_name': listing.crop_name,
                'price': float(listing.price),
                'quantity': listing.quantity,
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
