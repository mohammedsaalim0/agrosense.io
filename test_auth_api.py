#!/usr/bin/env python
import os
import django
import requests

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrosense_project.settings')
django.setup()

from django.contrib.auth import authenticate

# Test authentication
print("Testing authentication...")
user = authenticate(username='admin', password='admin123')
if user:
    print(f"✅ Authentication successful for user: {user.username}")
    
    # Now test the API endpoint
    print("\nTesting Razorpay order creation endpoint...")
    
    # Use Django test client to simulate authenticated request
    from django.test import Client
    
    client = Client()
    client.login(username='admin', password='admin123')
    
    response = client.post('/api/create-razorpay-order/', {
        'total_amount': 100.00,
    })
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
else:
    print("❌ Authentication failed")
