from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import CropEnvironment, IoTDevice, SensorReading, ActuatorState, IrrigationSchedule, ChamberControlLog, SystemAlert
from django.utils import timezone
import random

class Command(BaseCommand):
    help = 'Setup sample data for Smart IoT Chamber system'

    def handle(self, *args, **options):
        self.stdout.write('Setting up Smart IoT Chamber sample data...')
        
        # Get or create a test user
        user, created = User.objects.get_or_create(
            username='testuser',
            defaults={'email': 'test@example.com', 'is_staff': True}
        )
        if created:
            user.set_password('testpass123')
            user.save()
            self.stdout.write('Created test user: testuser/testpass123')
        
        # Create Crop Environments
        crop_envs = [
            {
                'name': 'Tomato',
                'scientific_name': 'Solanum lycopersicum',
                'description': 'Ideal greenhouse tomato with controlled temperature and humidity',
                'optimal_temperature': 25.0,
                'temperature_tolerance': 2.0,
                'optimal_humidity': 65.0,
                'humidity_tolerance': 5.0,
                'optimal_moisture': 70.0,
                'moisture_tolerance': 10.0,
                'light_hours': 16,
                'light_intensity': 400,
                'growth_stage_days': {'seedling': 10, 'vegetative': 21, 'flowering': 14, 'fruiting': 20},
                'water_consumption': 1.5
            },
            {
                'name': 'Lettuce',
                'scientific_name': 'Lactuca sativa',
                'description': 'Crisp lettuce perfect for controlled environment agriculture',
                'optimal_temperature': 18.0,
                'temperature_tolerance': 2.0,
                'optimal_humidity': 70.0,
                'humidity_tolerance': 5.0,
                'optimal_moisture': 80.0,
                'moisture_tolerance': 10.0,
                'light_hours': 14,
                'light_intensity': 300,
                'growth_stage_days': {'seedling': 7, 'vegetative': 14, 'maturity': 21},
                'water_consumption': 1.0
            },
            {
                'name': 'Strawberry',
                'scientific_name': 'Fragaria × ananassa',
                'description': 'Sweet strawberries grown in controlled environment',
                'optimal_temperature': 22.0,
                'temperature_tolerance': 2.0,
                'optimal_humidity': 75.0,
                'humidity_tolerance': 5.0,
                'optimal_moisture': 75.0,
                'moisture_tolerance': 10.0,
                'light_hours': 14,
                'light_intensity': 350,
                'growth_stage_days': {'seedling': 14, 'vegetative': 21, 'flowering': 28, 'fruiting': 35},
                'water_consumption': 1.2
            }
        ]
        
        for crop_data in crop_envs:
            crop, created = CropEnvironment.objects.get_or_create(
                name=crop_data['name'],
                defaults=crop_data
            )
            if created:
                self.stdout.write(f'Created crop environment: {crop.name}')
        
        # Create IoT Devices
        devices = [
            {
                'device_id': 'chamber_001',
                'name': 'Main Growth Chamber',
                'device_type': 'growth_chamber',
                'location': 'Greenhouse A',
                'description': 'Primary growth chamber for tomato cultivation',
                'configuration': {
                    'active_crop': 'Tomato',
                    'crop_environment_id': CropEnvironment.objects.get(name='Tomato').id,
                    'environment_set_at': timezone.now().isoformat()
                },
                'is_online': True,
                'last_seen': timezone.now()
            },
            {
                'device_id': 'chamber_002',
                'name': 'Secondary Growth Chamber',
                'device_type': 'growth_chamber',
                'location': 'Greenhouse B',
                'description': 'Secondary chamber for lettuce cultivation',
                'configuration': {
                    'active_crop': 'Lettuce',
                    'crop_environment_id': CropEnvironment.objects.get(name='Lettuce').id,
                    'environment_set_at': timezone.now().isoformat()
                },
                'is_online': True,
                'last_seen': timezone.now()
            }
        ]
        
        for device_data in devices:
            device, created = IoTDevice.objects.get_or_create(
                device_id=device_data['device_id'],
                defaults=device_data
            )
            if created:
                self.stdout.write(f'Created device: {device.name}')
        
        # Create sample sensor readings for each device
        for device in IoTDevice.objects.all():
            # Generate sample sensor data for the last 24 hours
            for hours_ago in range(24, 0, -1):
                timestamp = timezone.now() - timezone.timedelta(hours=hours_ago)
                
                # Temperature readings
                SensorReading.objects.get_or_create(
                    device=device,
                    sensor_type='temperature',
                    timestamp=timestamp,
                    defaults={
                        'value': round(random.uniform(20.0, 30.0), 1),
                        'unit': '°C',
                        'quality_score': random.uniform(0.8, 1.0)
                    }
                )
                
                # Humidity readings
                SensorReading.objects.get_or_create(
                    device=device,
                    sensor_type='humidity',
                    timestamp=timestamp,
                    defaults={
                        'value': round(random.uniform(50.0, 80.0), 1),
                        'unit': '%',
                        'quality_score': random.uniform(0.8, 1.0)
                    }
                )
                
                # Soil moisture readings
                SensorReading.objects.get_or_create(
                    device=device,
                    sensor_type='soil_moisture',
                    timestamp=timestamp,
                    defaults={
                        'value': round(random.uniform(40.0, 90.0), 1),
                        'unit': '%',
                        'quality_score': random.uniform(0.8, 1.0)
                    }
                )
                
                # Light readings
                SensorReading.objects.get_or_create(
                    device=device,
                    sensor_type='light',
                    timestamp=timestamp,
                    defaults={
                        'value': round(random.uniform(200.0, 600.0), 1),
                        'unit': 'lux',
                        'quality_score': random.uniform(0.8, 1.0)
                    }
                )
            
            # Create current actuator states
            actuators = ['water_pump', 'cooling_fan', 'grow_light', 'humidifier']
            for actuator_type in actuators:
                ActuatorState.objects.get_or_create(
                    device=device,
                    actuator_type=actuator_type,
                    defaults={
                        'is_active': random.choice([True, False]),
                        'power_level': random.randint(50, 100),
                        'control_mode': 'automatic',
                        'last_changed': timezone.now()
                    }
                )
        
        # Create sample irrigation schedules
        for device in IoTDevice.objects.all():
            IrrigationSchedule.objects.get_or_create(
                device=device,
                name='Morning Watering',
                defaults={
                    'start_time': '06:00:00',
                    'duration_minutes': 15,
                    'days_of_week': [1, 2, 3, 4, 5, 6, 7],
                    'moisture_threshold': 60.0,
                    'skip_rain': True,
                    'is_active': True
                }
            )
            
            IrrigationSchedule.objects.get_or_create(
                device=device,
                name='Evening Watering',
                defaults={
                    'start_time': '18:00:00',
                    'duration_minutes': 10,
                    'days_of_week': [1, 3, 5, 7],
                    'moisture_threshold': 55.0,
                    'skip_rain': True,
                    'is_active': True
                }
            )
        
        # Create sample control logs
        for device in IoTDevice.objects.all():
            for i in range(10):
                ChamberControlLog.objects.create(
                    device=device,
                    action_type=random.choice(['manual_control', 'automatic_control', 'schedule_trigger']),
                    description=f'Sample control action {i+1}',
                    target_actuator=random.choice(actuators),
                    old_value={'is_active': not random.choice([True, False])},
                    new_value={'is_active': random.choice([True, False]), 'power_level': random.randint(50, 100)},
                    user=user if random.choice([True, False]) else None,
                    source=random.choice(['web_dashboard', 'mqtt_command', 'schedule']),
                    success=True
                )
        
        # Create sample alerts
        alert_types = [
            ('temperature_high', 'warning', 'High Temperature Alert', 'Temperature exceeds optimal range'),
            ('humidity_low', 'info', 'Low Humidity Alert', 'Humidity below optimal range'),
            ('moisture_low', 'warning', 'Low Soil Moisture', 'Soil moisture below threshold'),
            ('device_offline', 'error', 'Device Offline', 'Device communication lost'),
            ('pump_failure', 'error', 'Pump Failure', 'Water pump not responding')
        ]
        
        for device in IoTDevice.objects.all():
            for alert_type, severity, title, message in alert_types:
                if random.choice([True, False]):  # Randomly create some alerts
                    SystemAlert.objects.create(
                        device=device,
                        alert_type=alert_type,
                        severity=severity,
                        title=title,
                        message=message,
                        details=f'Detailed information for {title}',
                        is_acknowledged=random.choice([True, False]),
                        acknowledged_by=user if random.choice([True, False]) else None,
                        is_resolved=random.choice([True, False])
                    )
        
        self.stdout.write(self.style.SUCCESS('Smart IoT Chamber sample data setup completed!'))
        self.stdout.write('Available devices:')
        for device in IoTDevice.objects.all():
            self.stdout.write(f'  - {device.device_id}: {device.name} ({device.get_device_type_display()})')
        
        self.stdout.write('Available crop environments:')
        for crop in CropEnvironment.objects.all():
            self.stdout.write(f'  - {crop.name}: {crop.optimal_temperature}°C, {crop.optimal_humidity}% humidity')
