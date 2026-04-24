from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    dob = models.DateField(null=True, blank=True)
    profession = models.CharField(max_length=100, blank=True, null=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"

class Crop(models.Model):
    name = models.CharField(max_length=100)
    suitability_score = models.IntegerField(default=0)
    yield_estimate = models.FloatField(default=0.0)
    description = models.TextField(blank=True, null=True)
    image_url = models.URLField(blank=True, null=True)

class SupportScheme(models.Model):
    title = models.CharField(max_length=200)
    provider = models.CharField(max_length=100)
    amount = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    category = models.CharField(max_length=50, default='General', blank=True, null=True)

class MarketListing(models.Model):
    crop_name = models.CharField(max_length=100)
    quantity = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    seller_name = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    quality = models.CharField(max_length=50, default='Standard') # Standard, Premium, A-Grade
    image_url = models.URLField(max_length=500, blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

class SchemeApplication(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending Review'),
        ('VERIFYING', 'Verifying Documents'),
        ('APPROVED', 'Approved'),
        ('DISBURSED', 'Funds Disbursed'),
        ('REJECTED', 'Rejected'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    scheme_name = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    applied_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.scheme_name}"


class LearningProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course_key = models.CharField(max_length=120)
    progress = models.PositiveSmallIntegerField(default=0)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'course_key')

    def __str__(self):
        return f"{self.user.username} - {self.course_key} ({self.progress}%)"


class CourseCertificate(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course_key = models.CharField(max_length=120)
    course_title = models.CharField(max_length=250)
    certificate_code = models.CharField(max_length=32, unique=True)
    issued_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'course_key')

    def __str__(self):
        return f"{self.user.username} - {self.course_title}"


class CourseAssessment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course_key = models.CharField(max_length=120)
    score = models.PositiveSmallIntegerField(default=0)
    passed = models.BooleanField(default=False)
    attempted_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'course_key')

    def __str__(self):
        return f"{self.user.username} - {self.course_key} ({self.score}%)"

class Product(models.Model):
    CATEGORY_CHOICES = [
        ('Fertilizers', 'Fertilizers'),
        ('Seeds', 'Seeds & Planting Material'),
        ('Pesticides', 'Pesticides & Insecticides'),
        ('Tools', 'Farming Tools & Equipment'),
        ('Organic', 'Organic Products'),
        ('Irrigation', 'Irrigation & Sprinklers'),
        ('Soil', 'Soil Testing Kits'),
        ('Marketplace', 'Farmers Marketplace'),
    ]
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    image_url = models.URLField(max_length=500, blank=True, null=True, help_text="Public URL for product image")
    image_upload = models.ImageField(upload_to='products/', blank=True, null=True, help_text="Upload product image directly (overrides URL above)")
    mrp = models.DecimalField(max_digits=10, decimal_places=2)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity_weight = models.CharField(max_length=100)
    rating = models.FloatField(default=4.5)
    is_organic = models.BooleanField(default=False)
    description = models.TextField(blank=True, null=True, help_text="Product description shown in the store")
    in_stock = models.BooleanField(default=True)

    def get_image(self):
        if self.image_upload:
            return self.image_upload.url
        return self.image_url or 'https://placehold.co/600x400/4E6E5D/ffffff?text=No+Image'

    def __str__(self):
        return self.name

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order_id = models.CharField(max_length=20, unique=True)
    full_name = models.CharField(max_length=200)
    address = models.TextField()
    pincode = models.CharField(max_length=10)
    phone = models.CharField(max_length=15)
    payment_method = models.CharField(max_length=50)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, default='PENDING') # PENDING, PAID, CANCELLED, SHIPPED, DELIVERED
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.order_id} - {self.full_name}"

class BankTransaction(models.Model):
    """Simulates a real bank statement record for automated UTR verification."""
    utr_id = models.CharField(max_length=12, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    sender_name = models.CharField(max_length=100)
    is_used = models.BooleanField(default=False)
    received_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"UTR {self.utr_id} - ₹{self.amount} ({'Used' if self.is_used else 'Available'})"

class VolunteerTask(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    location = models.CharField(max_length=200)
    points = models.IntegerField(default=10)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class VolunteerParticipation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    task = models.ForeignKey(VolunteerTask, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, default='JOINED') # JOINED, COMPLETED
    joined_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.task.title}"

