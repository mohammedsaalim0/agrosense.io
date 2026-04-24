import os
import sys
import django

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrosense_project.settings')
django.setup()

import ssl
import smtplib
from django.core.mail import send_mail
from django.conf import settings

# Monkeypatch smtplib to skip SSL verification
old_smtp_connect = smtplib.SMTP.connect
def new_smtp_connect(self, host='localhost', port=0, source_address=None, timeout=socket._GLOBAL_DEFAULT_TIMEOUT):
    return old_smtp_connect(self, host, port, source_address, timeout)
# Actually it's easier to just pass the context if we were using smtplib directly.
# For Django, we can try to set the context in settings or via a custom backend.

try:
    print(f"Attempting to send test email from {settings.EMAIL_HOST_USER}...")
    send_mail(
        subject="AgroSense Connection Test",
        message="This is a test email to verify the connection.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=["agrosensetumkur@gmail.com"],
        fail_silently=False,
    )
    print("SUCCESS: Email sent successfully!")
except Exception as e:
    print(f"FAILED: Could not send email. Error: {str(e)}")
