import smtplib
import ssl

sender_email = "agrosensetumkur@gmail.com"
receiver_email = "agrosensetumkur@gmail.com"
password = "xehuobqqcukidmnd"

message = """\
Subject: AgroSense Raw SMTP Test
This is a test message from AgroSense."""

context = ssl._create_unverified_context()

try:
    print("Connecting to Gmail SMTP server...")
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls(context=context)
        print("Logging in...")
        server.login(sender_email, password)
        print("Sending email...")
        server.sendmail(sender_email, receiver_email, message)
    print("SUCCESS: Raw SMTP email sent!")
except Exception as e:
    print(f"FAILED: Raw SMTP failed. Error: {str(e)}")
