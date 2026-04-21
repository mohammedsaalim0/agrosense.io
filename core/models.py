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
