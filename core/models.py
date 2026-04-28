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


class RefundRequest(models.Model):
    """Stores refund requests submitted by users for their orders."""
    STATUS_CHOICES = [
        ('PENDING', 'Pending Review'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('PROCESSED', 'Processed'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='refund_requests')
    refund_id = models.CharField(max_length=20, unique=True)
    request_type = models.CharField(
        max_length=10, 
        choices=[('REFUND', 'Refund'), ('EXCHANGE', 'Exchange')], 
        default='REFUND'
    )
    reason_category = models.CharField(max_length=100)
    reason_details = models.TextField()
    evidence_image = models.ImageField(upload_to='refund_evidence/', blank=True, null=True)
    # Payment details for refund
    payment_preference = models.CharField(max_length=10, default='UPI')  # UPI or BANK
    upi_id = models.CharField(max_length=100, blank=True, null=True)
    bank_account_no = models.CharField(max_length=20, blank=True, null=True)
    bank_ifsc = models.CharField(max_length=20, blank=True, null=True)
    bank_account_name = models.CharField(max_length=100, blank=True, null=True)
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Refund {self.refund_id} - Order {self.order.order_id} - {self.status}"


# Smart IoT Chamber System Models
class CropEnvironment(models.Model):
    """Crop-specific environmental requirements"""
    name = models.CharField(max_length=100, unique=True)
    scientific_name = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    
    # Environmental requirements
    optimal_temperature = models.FloatField(help_text="Optimal temperature in Celsius")
    temperature_tolerance = models.FloatField(default=2.0, help_text="Temperature tolerance ±°C")
    optimal_humidity = models.FloatField(help_text="Optimal humidity percentage")
    humidity_tolerance = models.FloatField(default=5.0, help_text="Humidity tolerance ±%")
    optimal_moisture = models.FloatField(help_text="Optimal soil moisture percentage")
    moisture_tolerance = models.FloatField(default=10.0, help_text="Moisture tolerance ±%")
    light_hours = models.IntegerField(default=16, help_text="Required light hours per day")
    light_intensity = models.IntegerField(default=300, help_text="Light intensity in µmol/m²/s")
    
    # Growth parameters
    growth_stage_days = models.JSONField(default=dict, help_text="Days per growth stage")
    water_consumption = models.FloatField(default=1.0, help_text="Daily water consumption in liters")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = "Crop Environment"
        verbose_name_plural = "Crop Environments"
    
    def __str__(self):
        return f"{self.name} (T:{self.optimal_temperature}°C, H:{self.optimal_humidity}%)"


class IoTDevice(models.Model):
    """IoT device management"""
    DEVICE_TYPES = [
        ('chamber', 'Growth Chamber'),
        ('irrigation', 'Irrigation System'),
        ('sensor', 'Sensor Node'),
    ]
    
    device_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    device_type = models.CharField(max_length=20, choices=DEVICE_TYPES)
    location = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    
    # Network information
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    mac_address = models.CharField(max_length=17, blank=True)
    last_seen = models.DateTimeField(null=True, blank=True)
    is_online = models.BooleanField(default=False)
    
    # Configuration
    mqtt_topic = models.CharField(max_length=200, blank=True)
    configuration = models.JSONField(default=dict, help_text="Device configuration")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['device_id']
        verbose_name = "IoT Device"
        verbose_name_plural = "IoT Devices"
    
    def __str__(self):
        return f"{self.name} ({self.device_id})"


class SensorReading(models.Model):
    """Real-time sensor data from IoT devices"""
    SENSOR_TYPES = [
        ('temperature', 'Temperature'),
        ('humidity', 'Humidity'),
        ('soil_moisture', 'Soil Moisture'),
        ('light', 'Light Intensity'),
        ('ph', 'pH Level'),
        ('ec', 'Electrical Conductivity'),
    ]
    
    device = models.ForeignKey(IoTDevice, on_delete=models.CASCADE, related_name='sensor_readings')
    sensor_type = models.CharField(max_length=20, choices=SENSOR_TYPES)
    value = models.FloatField()
    unit = models.CharField(max_length=10, help_text="Measurement unit (°C, %, lux, etc.)")
    
    # Quality indicators
    quality_score = models.FloatField(default=100.0, help_text="Data quality score 0-100")
    is_anomaly = models.BooleanField(default=False, help_text="Flagged as anomalous reading")
    
    # Timestamps
    timestamp = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['device', 'sensor_type', '-timestamp']),
            models.Index(fields=['timestamp']),
        ]
        verbose_name = "Sensor Reading"
        verbose_name_plural = "Sensor Readings"
    
    def __str__(self):
        return f"{self.device.name} - {self.sensor_type}: {self.value}{self.unit}"


class ActuatorState(models.Model):
    """Current state of actuators (pumps, fans, lights, etc.)"""
    ACTUATOR_TYPES = [
        ('water_pump', 'Water Pump'),
        ('cooling_fan', 'Cooling Fan'),
        ('heater', 'Heater'),
        ('grow_light', 'Grow Light'),
        ('humidifier', 'Humidifier'),
        ('ventilation', 'Ventilation'),
    ]
    
    device = models.ForeignKey(IoTDevice, on_delete=models.CASCADE, related_name='actuator_states')
    actuator_type = models.CharField(max_length=20, choices=ACTUATOR_TYPES)
    is_active = models.BooleanField(default=False)
    power_level = models.IntegerField(default=0, help_text="Power level 0-100%")
    
    # Control information
    control_mode = models.CharField(max_length=20, default='auto', choices=[
        ('auto', 'Automatic'),
        ('manual', 'Manual'),
        ('scheduled', 'Scheduled'),
    ])
    
    # Timestamps
    last_changed = models.DateTimeField(auto_now=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['device', 'actuator_type']
        unique_together = ['device', 'actuator_type']
        verbose_name = "Actuator State"
        verbose_name_plural = "Actuator States"
    
    def __str__(self):
        status = "ON" if self.is_active else "OFF"
        return f"{self.device.name} - {self.get_actuator_type_display()}: {status} ({self.power_level}%)"


class IrrigationSchedule(models.Model):
    """Automated irrigation scheduling"""
    device = models.ForeignKey(IoTDevice, on_delete=models.CASCADE, related_name='irrigation_schedules')
    name = models.CharField(max_length=100)
    
    # Schedule configuration
    start_time = models.TimeField()
    duration_minutes = models.IntegerField(help_text="Duration in minutes")
    days_of_week = models.JSONField(default=list, help_text="Days of week [1,2,3,4,5]")
    
    # Conditions
    moisture_threshold = models.FloatField(null=True, blank=True, help_text="Only irrigate if moisture below this")
    skip_rain = models.BooleanField(default=True, help_text="Skip irrigation on rainy days")
    
    # Status
    is_active = models.BooleanField(default=True)
    last_run = models.DateTimeField(null=True, blank=True)
    next_run = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['device', 'start_time']
        verbose_name = "Irrigation Schedule"
        verbose_name_plural = "Irrigation Schedules"
    
    def __str__(self):
        return f"{self.device.name} - {self.name} at {self.start_time}"


class ChamberControlLog(models.Model):
    """Audit log for all control actions"""
    ACTION_TYPES = [
        ('manual_control', 'Manual Control'),
        ('auto_control', 'Automatic Control'),
        ('schedule_trigger', 'Schedule Trigger'),
        ('emergency_stop', 'Emergency Stop'),
        ('system_error', 'System Error'),
        ('calibration', 'Calibration'),
    ]
    
    device = models.ForeignKey(IoTDevice, on_delete=models.CASCADE, related_name='control_logs')
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    
    # Action details
    description = models.TextField()
    target_actuator = models.CharField(max_length=20, blank=True)
    old_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField(null=True, blank=True)
    
    # User information
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    source = models.CharField(max_length=50, default='system', help_text="Source of the action")
    
    # Result
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    
    # Timestamps
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['device', '-timestamp']),
            models.Index(fields=['action_type', '-timestamp']),
        ]
        verbose_name = "Control Log"
        verbose_name_plural = "Control Logs"
    
    def __str__(self):
        return f"{self.device.name} - {self.get_action_type_display()} at {self.timestamp}"


class SystemAlert(models.Model):
    """System alerts and notifications"""
    SEVERITY_LEVELS = [
        ('info', 'Information'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical'),
    ]
    
    ALERT_TYPES = [
        ('sensor_failure', 'Sensor Failure'),
        ('actuator_failure', 'Actuator Failure'),
        ('network_disconnected', 'Network Disconnected'),
        ('power_failure', 'Power Failure'),
        ('environmental_extreme', 'Environmental Extreme'),
        ('maintenance_required', 'Maintenance Required'),
        ('security_breach', 'Security Breach'),
    ]
    
    device = models.ForeignKey(IoTDevice, on_delete=models.CASCADE, related_name='alerts', null=True, blank=True)
    alert_type = models.CharField(max_length=30, choices=ALERT_TYPES)
    severity = models.CharField(max_length=10, choices=SEVERITY_LEVELS)
    
    # Alert details
    title = models.CharField(max_length=200)
    message = models.TextField()
    details = models.JSONField(default=dict, blank=True)
    
    # Status
    is_acknowledged = models.BooleanField(default=False)
    acknowledged_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['severity', '-created_at']),
            models.Index(fields=['is_resolved', '-created_at']),
        ]
        verbose_name = "System Alert"
        verbose_name_plural = "System Alerts"
    
    def __str__(self):
        return f"{self.get_severity_display()}: {self.title}"

