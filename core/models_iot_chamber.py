"""
Smart IoT Chamber Database Models
Production-ready models for precision agriculture IoT system
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
import json


class IoTDevice(models.Model):
    """
    IoT Device model for managing growth chambers and irrigation systems
    """
    DEVICE_TYPES = [
        ('growth_chamber', 'Growth Chamber'),
        ('irrigation_system', 'Irrigation System'),
        ('sensor_node', 'Sensor Node'),
        ('actuator_node', 'Actuator Node'),
    ]
    
    STATUS_CHOICES = [
        ('online', 'Online'),
        ('offline', 'Offline'),
        ('maintenance', 'Maintenance'),
        ('error', 'Error'),
    ]
    
    device_id = models.CharField(max_length=50, unique=True, help_text="Unique device identifier")
    name = models.CharField(max_length=100, help_text="Human-readable device name")
    device_type = models.CharField(max_length=20, choices=DEVICE_TYPES, default='growth_chamber')
    location = models.CharField(max_length=100, blank=True, help_text="Physical location of device")
    description = models.TextField(blank=True, help_text="Device description and purpose")
    
    # Status and connectivity
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='offline')
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(null=True, blank=True)
    last_heartbeat = models.DateTimeField(null=True, blank=True)
    
    # Configuration and settings
    configuration = models.JSONField(default=dict, help_text="Device configuration and settings")
    firmware_version = models.CharField(max_length=20, blank=True)
    hardware_version = models.CharField(max_length=20, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        db_table = 'core_iotdevice'
        indexes = [
            models.Index(fields=['device_id']),
            models.Index(fields=['status']),
            models.Index(fields=['last_seen']),
            models.Index(fields=['device_type']),
        ]
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.device_id})"
    
    def get_device_type_display(self):
        return dict(self.DEVICE_TYPES).get(self.device_type, self.device_type)
    
    def update_heartbeat(self):
        """Update device heartbeat timestamp"""
        self.last_heartbeat = timezone.now()
        self.is_online = True
        self.status = 'online'
        self.save(update_fields=['last_heartbeat', 'is_online', 'status'])


class CropEnvironment(models.Model):
    """
    Crop environment profiles with optimal growing conditions
    """
    name = models.CharField(max_length=100, help_text="Crop name")
    scientific_name = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True, help_text="Crop description and growing notes")
    
    # Optimal conditions
    optimal_temperature = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(50)],
        help_text="Optimal temperature in Celsius"
    )
    temperature_tolerance = models.FloatField(
        default=2.0,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        help_text="Temperature tolerance in Celsius"
    )
    
    optimal_humidity = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Optimal humidity percentage"
    )
    humidity_tolerance = models.FloatField(
        default=5.0,
        validators=[MinValueValidator(0), MaxValueValidator(20)],
        help_text="Humidity tolerance percentage"
    )
    
    optimal_soil_moisture = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Optimal soil moisture percentage"
    )
    moisture_tolerance = models.FloatField(
        default=10.0,
        validators=[MinValueValidator(0), MaxValueValidator(30)],
        help_text="Moisture tolerance percentage"
    )
    
    # Light requirements
    light_hours = models.IntegerField(
        default=16,
        validators=[MinValueValidator(0), MaxValueValidator(24)],
        help_text="Required light hours per day"
    )
    light_intensity = models.IntegerField(
        default=400,
        validators=[MinValueValidator(0), MaxValueValidator(2000)],
        help_text="Required light intensity in lux"
    )
    
    # Growth stages
    growth_stages = models.JSONField(
        default=dict,
        help_text="Growth stage durations in days"
    )
    
    # Water and nutrient requirements
    water_consumption = models.FloatField(
        default=1.0,
        validators=[MinValueValidator(0)],
        help_text="Daily water consumption in liters"
    )
    
    # Metadata
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        db_table = 'core_cropenvironment'
        ordering = ['name']
        verbose_name = "Crop Environment"
        verbose_name_plural = "Crop Environments"
    
    def __str__(self):
        return f"{self.name} ({self.scientific_name})"
    
    def get_temperature_range(self):
        """Get acceptable temperature range"""
        return {
            'min': self.optimal_temperature - self.temperature_tolerance,
            'max': self.optimal_temperature + self.temperature_tolerance
        }
    
    def get_humidity_range(self):
        """Get acceptable humidity range"""
        return {
            'min': self.optimal_humidity - self.humidity_tolerance,
            'max': self.optimal_humidity + self.humidity_tolerance
        }
    
    def get_moisture_range(self):
        """Get acceptable moisture range"""
        return {
            'min': self.optimal_soil_moisture - self.moisture_tolerance,
            'max': self.optimal_soil_moisture + self.moisture_tolerance
        }


class SensorReading(models.Model):
    """
    Time-series sensor readings from IoT devices
    """
    SENSOR_TYPES = [
        ('temperature', 'Temperature'),
        ('humidity', 'Humidity'),
        ('soil_moisture', 'Soil Moisture'),
        ('light', 'Light Intensity'),
        ('ph', 'pH Level'),
        ('ec', 'Electrical Conductivity'),
        ('co2', 'CO2 Level'),
        ('pressure', 'Atmospheric Pressure'),
    ]
    
    device = models.ForeignKey(IoTDevice, on_delete=models.CASCADE, related_name='sensor_readings')
    sensor_type = models.CharField(max_length=20, choices=SENSOR_TYPES)
    
    # Reading values
    value = models.FloatField(help_text="Sensor reading value")
    unit = models.CharField(max_length=20, help_text="Unit of measurement")
    
    # Quality and metadata
    quality_score = models.FloatField(
        default=1.0,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Data quality score (0-1)"
    )
    raw_value = models.FloatField(null=True, blank=True, help_text="Raw sensor value before calibration")
    
    # Timestamps
    timestamp = models.DateTimeField(default=timezone.now, help_text="Reading timestamp")
    received_at = models.DateTimeField(auto_now_add=True, help_text="When reading was received")
    
    class Meta:
        db_table = 'core_sensorreading'
        indexes = [
            models.Index(fields=['device', 'sensor_type', 'timestamp']),
            models.Index(fields=['sensor_type', 'timestamp']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['device', 'timestamp']),
        ]
        ordering = ['-timestamp']
        verbose_name = "Sensor Reading"
        verbose_name_plural = "Sensor Readings"
    
    def __str__(self):
        return f"{self.device.name} - {self.sensor_type}: {self.value}{self.unit}"
    
    @classmethod
    def get_latest_readings(cls, device_id, sensor_types=None):
        """Get latest readings for specified sensor types"""
        queryset = cls.objects.filter(device__device_id=device_id)
        if sensor_types:
            queryset = queryset.filter(sensor_type__in=sensor_types)
        
        latest_readings = {}
        for sensor_type in (sensor_types or [s[0] for s in cls.SENSOR_TYPES]):
            latest = queryset.filter(sensor_type=sensor_type).first()
            if latest:
                latest_readings[sensor_type] = latest
        
        return latest_readings


class ActuatorState(models.Model):
    """
    Current state of actuators (pumps, fans, lights, etc.)
    """
    ACTUATOR_TYPES = [
        ('water_pump', 'Water Pump'),
        ('nutrient_pump', 'Nutrient Pump'),
        ('cooling_fan', 'Cooling Fan'),
        ('heating_element', 'Heating Element'),
        ('grow_light', 'Grow Light'),
        ('humidifier', 'Humidifier'),
        ('dehumidifier', 'Dehumidifier'),
        ('ventilation', 'Ventilation Fan'),
        ('co2_injector', 'CO2 Injector'),
    ]
    
    device = models.ForeignKey(IoTDevice, on_delete=models.CASCADE, related_name='actuator_states')
    actuator_type = models.CharField(max_length=20, choices=ACTUATOR_TYPES)
    
    # State information
    is_active = models.BooleanField(default=False, help_text="Whether actuator is currently active")
    power_level = models.IntegerField(
        default=100,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Power level percentage (0-100)"
    )
    
    # Control mode
    control_mode = models.CharField(
        max_length=20,
        choices=[
            ('manual', 'Manual'),
            ('automatic', 'Automatic'),
            ('scheduled', 'Scheduled'),
            ('emergency', 'Emergency'),
        ],
        default='automatic'
    )
    
    # Runtime tracking
    total_runtime = models.IntegerField(default=0, help_text="Total runtime in seconds")
    cycle_count = models.IntegerField(default=0, help_text="Number of activation cycles")
    
    # Timestamps
    last_changed = models.DateTimeField(auto_now=True, help_text="Last state change timestamp")
    last_activated = models.DateTimeField(null=True, blank=True, help_text="Last activation timestamp")
    
    class Meta:
        db_table = 'core_actuatorstate'
        indexes = [
            models.Index(fields=['device', 'actuator_type']),
            models.Index(fields=['actuator_type', 'is_active']),
            models.Index(fields=['last_changed']),
        ]
        unique_together = ['device', 'actuator_type']
        verbose_name = "Actuator State"
        verbose_name_plural = "Actuator States"
    
    def __str__(self):
        status = "ON" if self.is_active else "OFF"
        return f"{self.device.name} - {self.get_actuator_type_display()}: {status} ({self.power_level}%)"
    
    def activate(self, power_level=100):
        """Activate actuator with specified power level"""
        self.is_active = True
        self.power_level = power_level
        self.last_activated = timezone.now()
        self.cycle_count += 1
        self.save()
    
    def deactivate(self):
        """Deactivate actuator"""
        if self.is_active:
            # Update runtime
            if self.last_activated:
                runtime = (timezone.now() - self.last_activated).total_seconds()
                self.total_runtime += int(runtime)
        
        self.is_active = False
        self.power_level = 0
        self.save()


class IrrigationSchedule(models.Model):
    """
    Automated irrigation schedules for devices
    """
    device = models.ForeignKey(IoTDevice, on_delete=models.CASCADE, related_name='irrigation_schedules')
    name = models.CharField(max_length=100, help_text="Schedule name")
    
    # Timing
    start_time = models.TimeField(help_text="Daily start time")
    duration_minutes = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(60)],
        help_text="Irrigation duration in minutes"
    )
    
    # Schedule pattern
    days_of_week = models.JSONField(
        default=list,
        help_text="Days of week (1=Monday, 7=Sunday)"
    )
    
    # Conditions and thresholds
    moisture_threshold = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Soil moisture threshold to trigger irrigation"
    )
    skip_rain = models.BooleanField(default=True, help_text="Skip irrigation if rain detected")
    
    # Status
    is_active = models.BooleanField(default=True)
    last_run = models.DateTimeField(null=True, blank=True)
    next_run = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        db_table = 'core_irrigationschedule'
        ordering = ['start_time']
        verbose_name = "Irrigation Schedule"
        verbose_name_plural = "Irrigation Schedules"
    
    def __str__(self):
        return f"{self.device.name} - {self.name} ({self.start_time})"
    
    def should_run_today(self):
        """Check if schedule should run today"""
        today = timezone.now().weekday() + 1  # Convert to 1-7 format
        return today in self.days_of_week and self.is_active


class ChamberControlLog(models.Model):
    """
    Audit log of all control actions and system events
    """
    ACTION_TYPES = [
        ('manual_control', 'Manual Control'),
        ('automatic_control', 'Automatic Control'),
        ('schedule_trigger', 'Schedule Trigger'),
        ('alert_triggered', 'Alert Triggered'),
        ('system_event', 'System Event'),
        ('emergency_stop', 'Emergency Stop'),
        ('configuration_change', 'Configuration Change'),
    ]
    
    device = models.ForeignKey(IoTDevice, on_delete=models.CASCADE, related_name='control_logs')
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    
    # Action details
    description = models.CharField(max_length=200, help_text="Action description")
    target_actuator = models.CharField(max_length=20, blank=True, help_text="Target actuator if applicable")
    
    # State changes
    old_value = models.JSONField(null=True, blank=True, help_text="Previous state")
    new_value = models.JSONField(null=True, blank=True, help_text="New state")
    
    # Execution details
    success = models.BooleanField(default=True, help_text="Whether action was successful")
    error_message = models.TextField(blank=True, help_text="Error message if action failed")
    execution_time_ms = models.IntegerField(null=True, blank=True, help_text="Execution time in milliseconds")
    
    # Source and user
    source = models.CharField(
        max_length=20,
        choices=[
            ('web_dashboard', 'Web Dashboard'),
            ('mqtt_command', 'MQTT Command'),
            ('schedule', 'Schedule'),
            ('automatic', 'Automatic System'),
            ('mobile_app', 'Mobile App'),
        ],
        default='automatic'
    )
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Timestamps
    timestamp = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'core_chambercontrollog'
        indexes = [
            models.Index(fields=['device', 'timestamp']),
            models.Index(fields=['action_type', 'timestamp']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['source']),
        ]
        ordering = ['-timestamp']
        verbose_name = "Control Log"
        verbose_name_plural = "Control Logs"
    
    def __str__(self):
        return f"{self.device.name} - {self.action_type}: {self.description}"


class SystemAlert(models.Model):
    """
    System alerts and notifications
    """
    ALERT_TYPES = [
        ('temperature_high', 'High Temperature'),
        ('temperature_low', 'Low Temperature'),
        ('humidity_high', 'High Humidity'),
        ('humidity_low', 'Low Humidity'),
        ('moisture_low', 'Low Soil Moisture'),
        ('moisture_high', 'High Soil Moisture'),
        ('light_low', 'Low Light'),
        ('device_offline', 'Device Offline'),
        ('pump_failure', 'Pump Failure'),
        ('sensor_error', 'Sensor Error'),
        ('power_failure', 'Power Failure'),
        ('network_error', 'Network Error'),
        ('maintenance_due', 'Maintenance Due'),
        ('system_error', 'System Error'),
    ]
    
    SEVERITY_LEVELS = [
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical'),
    ]
    
    device = models.ForeignKey(IoTDevice, on_delete=models.CASCADE, related_name='alerts', null=True, blank=True)
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    severity = models.CharField(max_length=10, choices=SEVERITY_LEVELS, default='warning')
    
    # Alert content
    title = models.CharField(max_length=100, help_text="Alert title")
    message = models.TextField(help_text="Alert message")
    details = models.JSONField(default=dict, help_text="Additional alert details")
    
    # Status and resolution
    is_acknowledged = models.BooleanField(default=False)
    acknowledged_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    
    is_resolved = models.BooleanField(default=False)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_alerts')
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)
    
    # Notifications
    notification_sent = models.BooleanField(default=False)
    notification_channels = models.JSONField(default=list, help_text="Channels where notification was sent")
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'core_systemalert'
        indexes = [
            models.Index(fields=['device', 'created_at']),
            models.Index(fields=['severity', 'is_resolved']),
            models.Index(fields=['alert_type', 'created_at']),
            models.Index(fields=['created_at']),
        ]
        ordering = ['-created_at']
        verbose_name = "System Alert"
        verbose_name_plural = "System Alerts"
    
    def __str__(self):
        return f"{self.get_severity_display()}: {self.title}"
    
    def acknowledge(self, user):
        """Acknowledge alert"""
        self.is_acknowledged = True
        self.acknowledged_by = user
        self.acknowledged_at = timezone.now()
        self.save()
    
    def resolve(self, user, notes=""):
        """Resolve alert"""
        self.is_resolved = True
        self.resolved_by = user
        self.resolved_at = timezone.now()
        self.resolution_notes = notes
        self.save()


class DeviceConfiguration(models.Model):
    """
    Device-specific configuration and calibration data
    """
    device = models.OneToOneField(IoTDevice, on_delete=models.CASCADE, related_name='configuration_profile')
    
    # Sensor calibration
    sensor_calibrations = models.JSONField(
        default=dict,
        help_text="Sensor calibration data (offsets, scales)"
    )
    
    # Actuator limits and safety
    max_pump_runtime = models.IntegerField(
        default=300,
        validators=[MinValueValidator(60), MaxValueValidator(3600)],
        help_text="Maximum pump runtime in seconds"
    )
    min_moisture_threshold = models.FloatField(
        default=20.0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Minimum soil moisture threshold"
    )
    max_temperature_limit = models.FloatField(
        default=40.0,
        validators=[MinValueValidator(0), MaxValueValidator(60)],
        help_text="Maximum temperature limit"
    )
    min_temperature_limit = models.FloatField(
        default=5.0,
        validators=[MinValueValidator(-10), MaxValueValidator(30)],
        help_text="Minimum temperature limit"
    )
    
    # Control parameters
    control_interval = models.IntegerField(
        default=30,
        validators=[MinValueValidator(5), MaxValueValidator(300)],
        help_text="Control loop interval in seconds"
    )
    data_publish_interval = models.IntegerField(
        default=10,
        validators=[MinValueValidator(5), MaxValueValidator(300)],
        help_text="Data publish interval in seconds"
    )
    
    # Safety features
    emergency_stop_enabled = models.BooleanField(default=True)
    watchdog_timeout = models.IntegerField(
        default=120,
        validators=[MinValueValidator(30), MaxValueValidator(600)],
        help_text="Watchdog timeout in seconds"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'core_deviceconfiguration'
        verbose_name = "Device Configuration"
        verbose_name_plural = "Device Configurations"
    
    def __str__(self):
        return f"{self.device.name} Configuration"
    
    def get_sensor_calibration(self, sensor_type):
        """Get calibration data for specific sensor"""
        return self.sensor_calibrations.get(sensor_type, {'offset': 0, 'scale': 1.0})
