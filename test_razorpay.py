#!/usr/bin/env python
import os
import django
import razorpay

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrosense_project.settings')
django.setup()

# Test Razorpay connection
from django.conf import settings

print("Testing Razorpay API connection...")
print(f"Key ID: {settings.RAZORPAY_KEY_ID}")
print(f"Key Secret: {'*' * len(settings.RAZORPAY_KEY_SECRET) if settings.RAZORPAY_KEY_SECRET else 'None'}")

try:
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    
    # Test creating a small order
    order_data = {
        'amount': 100,  # ₹1.00 in paise
        'currency': 'INR',
        'payment_capture': 1,
        'receipt': 'test_order_001'
    }
    
    print("\nCreating test order...")
    order = client.order.create(data=order_data)
    print(f"✅ Order created successfully!")
    print(f"Order ID: {order['id']}")
    print(f"Amount: {order['amount']} paise")
    
    # Test fetching order
    print("\nFetching order details...")
    fetched_order = client.order.fetch(order['id'])
    print(f"✅ Order fetched successfully!")
    print(f"Status: {fetched_order['status']}")
    
except Exception as e:
    print(f"❌ Error: {str(e)}")
    print(f"Error type: {type(e).__name__}")
    
    # Check if it's an authentication error
    if "401" in str(e) or "Unauthorized" in str(e):
        print("\n🔍 This appears to be an authentication error.")
        print("Please check:")
        print("1. RAZORPAY_KEY_ID is correct")
        print("2. RAZORPAY_KEY_SECRET is correct") 
        print("3. Both keys are from the same Razorpay account")
    
    # Check if it's a network error
    elif "connection" in str(e).lower() or "network" in str(e).lower():
        print("\n🔍 This appears to be a network connectivity error.")
        print("Please check:")
        print("1. Internet connection is working")
        print("2. Firewall is not blocking the request")
        print("3. Razorpay API is accessible")

print("\nTest completed.")
