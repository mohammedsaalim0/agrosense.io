"""
Smart IoT Irrigation & Environmental Control System
Backend API endpoints for ESP32 integration with Manual, Automatic, and Plant-Based control modes
"""

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
import json
import logging
from datetime import timedelta

logger = logging.getLogger(__name__)

# Mock models - In production, these would be real Django models
class IoTDevice:
    """Mock IoT Device model"""
    def __init__(self, device_id, name, location, is_active=True):
        self.device_id = device_id
        self.name = name
        self.location = location
        self.is_active = is_active
        self.last_seen = timezone.now()
        self.created_at = timezone.now()

class SensorReading:
    """Mock Sensor Reading model"""
    def __init__(self, device_id, sensor_type, value, timestamp=None):
        self.device_id = device_id
        self.sensor_type = sensor_type
        self.value = value
        self.timestamp = timestamp or timezone.now()

class DeviceCommand:
    """Mock Device Command model"""
    def __init__(self, device_id, command_type, parameters, user=None):
        self.device_id = device_id
        self.command_type = command_type
        self.parameters = parameters
        self.user = user
        self.created_at = timezone.now()
        self.executed = False

class PlantProfile:
    """Mock Plant Profile model"""
    def __init__(self, name, display_name, soil_moisture_min, soil_moisture_max, 
                 temperature_min, temperature_max, light_hours, light_intensity):
        self.name = name
        self.display_name = display_name
        self.soil_moisture_min = soil_moisture_min
        self.soil_moisture_max = soil_moisture_max
        self.temperature_min = temperature_min
        self.temperature_max = temperature_max
        self.light_hours = light_hours
        self.light_intensity = light_intensity

# Mock database storage
devices = {}
sensor_readings = []
device_commands = {}

# Predefined plant profiles
PLANT_PROFILES = {
    "tomato": PlantProfile(
        name="tomato",
        display_name="🍅 Tomato",
        soil_moisture_min=55.0,
        soil_moisture_max=75.0,
        temperature_min=18.0,
        temperature_max=32.0,
        light_hours=16,
        light_intensity=400
    ),
    "lettuce": PlantProfile(
        name="lettuce",
        display_name="🥬 Lettuce",
        soil_moisture_min=65.0,
        soil_moisture_max=80.0,
        temperature_min=12.0,
        temperature_max=28.0,
        light_hours=14,
        light_intensity=350
    ),
    "wheat": PlantProfile(
        name="wheat",
        display_name="🌾 Wheat",
        soil_moisture_min=60.0,
        soil_moisture_max=75.0,
        temperature_min=10.0,
        temperature_max=25.0,
        light_hours=12,
        light_intensity=300
    ),
    "rice": PlantProfile(
        name="rice",
        display_name="🌾 Rice",
        soil_moisture_min=70.0,
        soil_moisture_max=85.0,
        temperature_min=20.0,
        temperature_max=30.0,
        light_hours=14,
        light_intensity=250
    )
}

def get_or_create_device(device_id):
    """Get or create device by ID"""
    if device_id not in devices:
        devices[device_id] = IoTDevice(
            device_id=device_id,
            name=f"ESP32 Device {device_id}",
            location="Farm Field"
        )
    return devices[device_id]

def store_sensor_reading(device_id, sensor_type, value):
    """Store sensor reading in database"""
    reading = SensorReading(device_id=device_id, sensor_type=sensor_type, value=value)
    sensor_readings.append(reading)
    
    # Keep only last 1000 readings per device
    device_readings = [r for r in sensor_readings if r.device_id == device_id]
    if len(device_readings) > 1000:
        sensor_readings[:] = [r for r in sensor_readings if r.device_id != device_id][-1000:]

def store_device_command(device_id, command_type, parameters, user=None):
    """Store device command in database"""
    command = DeviceCommand(device_id=device_id, command_type=command_type, 
                        parameters=parameters, user=user)
    device_commands[device_id] = command
    return command

@csrf_exempt
@api_view(['POST'])
@permission_classes([])
def receive_sensor_data(request):
    """
    Receive sensor data from ESP32 device
    POST /api/sensor-data
    """
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id', 'unknown')
        
        # Get or create device
        device = get_or_create_device(device_id)
        device.last_seen = timezone.now()
        
        # Store sensor readings
        sensors = data.get('sensors', {})
        for sensor_type, value in sensors.items():
            store_sensor_reading(device_id, sensor_type, value)
        
        # Store device status
        device_status = data.get('device_status', {})
        if device_status:
            store_sensor_reading(device_id, 'wifi_rssi', device_status.get('wifi_rssi', 0))
            store_sensor_reading(device_id, 'free_heap', device_status.get('free_heap', 0))
            store_sensor_reading(device_id, 'uptime', device_status.get('uptime_seconds', 0))
        
        # Log the data
        logger.info(f"Received sensor data from {device_id}: {sensors}")
        
        return JsonResponse({
            'status': 'success',
            'message': 'Sensor data received successfully',
            'device_id': device_id,
            'timestamp': timezone.now().isoformat()
        })
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in sensor data: {e}")
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON data'
        }, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        logger.error(f"Error processing sensor data: {e}")
        return JsonResponse({
            'status': 'error',
            'message': 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def device_control_api(request):
    """
    Get control commands for ESP32 device
    GET /api/device-control?device_id=esp32_001
    """
    try:
        device_id = request.GET.get('device_id', 'esp32_001')
        
        # Get device
        device = get_or_create_device(device_id)
        
        # Get latest commands for this device
        commands = device_commands.get(device_id)
        
        # Default to AUTO mode if no commands
        mode = "AUTO"
        pump_active = False
        fan_active = False
        light_active = False
        plant_profile = "tomato"
        
        if commands:
            mode = commands.parameters.get('mode', 'AUTO')
            pump_active = commands.parameters.get('pump', False)
            fan_active = commands.parameters.get('fan', False)
            light_active = commands.parameters.get('light', False)
            plant_profile = commands.parameters.get('plant', 'tomato')
        
        # Get plant profile
        plant = PLANT_PROFILES.get(plant_profile, PLANT_PROFILES['tomato'])
        
        # Prepare response
        response_data = {
            'mode': mode,
            'commands': {
                'water_pump': pump_active,
                'cooling_fan': fan_active,
                'led_light': light_active,
                'duration': 30
            },
            'thresholds': {
                'soil_moisture_min': plant.soil_moisture_min,
                'soil_moisture_max': plant.soil_moisture_max,
                'temperature_min': plant.temperature_min,
                'temperature_max': plant.temperature_max,
                'light_min': plant.light_intensity - 100,
                'light_max': plant.light_intensity + 100
            },
            'plant_profile': {
                'name': plant.name,
                'display_name': plant.display_name,
                'optimal_conditions': {
                    'soil_moisture': (plant.soil_moisture_min + plant.soil_moisture_max) / 2,
                    'temperature': (plant.temperature_min + plant.temperature_max) / 2,
                    'humidity': 65,
                    'light_hours': plant.light_hours
                }
            }
        }
        
        logger.info(f"Device control request for {device_id}: mode={mode}")
        
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.error(f"Error in device control API: {e}")
        return JsonResponse({
            'status': 'error',
            'message': 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_device_command(request):
    """
    Send control command to ESP32 device
    POST /api/device-control
    """
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id', 'esp32_001')
        mode = data.get('mode', 'MANUAL')
        commands = data.get('commands', {})
        plant_profile = data.get('plant_profile', 'tomato')
        
        # Store command
        command = store_device_command(
            device_id=device_id,
            command_type='control_update',
            parameters={
                'mode': mode,
                'pump': commands.get('water_pump', False),
                'fan': commands.get('cooling_fan', False),
                'light': commands.get('led_light', False),
                'plant': plant_profile
            },
            user=request.user
        )
        
        logger.info(f"Command sent to {device_id}: {data}")
        
        return JsonResponse({
            'status': 'success',
            'message': 'Command sent successfully',
            'command_id': command.created_at.timestamp(),
            'device_id': device_id
        })
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in device command: {e}")
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON data'
        }, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        logger.error(f"Error sending device command: {e}")
        return JsonResponse({
            'status': 'error',
            'message': 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_sensor_history(request):
    """
    Get historical sensor data for charts
    GET /api/sensor-history?device_id=esp32_001&hours=24
    """
    try:
        device_id = request.GET.get('device_id', 'esp32_001')
        hours = int(request.GET.get('hours', 24))
        
        # Get sensor readings for the specified time period
        cutoff_time = timezone.now() - timedelta(hours=hours)
        device_readings_filtered = [
            r for r in sensor_readings 
            if r.device_id == device_id and r.timestamp >= cutoff_time
        ]
        
        # Group by sensor type
        sensor_data = {}
        for reading in device_readings_filtered:
            sensor_type = reading.sensor_type
            if sensor_type not in sensor_data:
                sensor_data[sensor_type] = []
            sensor_data[sensor_type].append({
                'timestamp': reading.timestamp.isoformat(),
                'value': reading.value
            })
        
        return JsonResponse({
            'status': 'success',
            'device_id': device_id,
            'hours': hours,
            'sensor_data': sensor_data,
            'total_readings': len(device_readings_filtered)
        })
        
    except ValueError as e:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid hours parameter'
        }, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        logger.error(f"Error getting sensor history: {e}")
        return JsonResponse({
            'status': 'error',
            'message': 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_device_status(request):
    """
    Get current device status and recent readings
    GET /api/device-status?device_id=esp32_001
    """
    try:
        device_id = request.GET.get('device_id', 'esp32_001')
        
        # Get device
        device = get_or_create_device(device_id)
        
        # Get latest sensor readings
        device_readings_filtered = [
            r for r in sensor_readings if r.device_id == device_id
        ]
        
        # Get latest readings by sensor type
        latest_readings = {}
        for reading in device_readings_filtered[-20:]:  # Last 20 readings
            sensor_type = reading.sensor_type
            if sensor_type not in latest_readings or reading.timestamp > latest_readings[sensor_type]['timestamp']:
                latest_readings[sensor_type] = {
                    'value': reading.value,
                    'timestamp': reading.timestamp.isoformat()
                }
        
        # Get latest command
        latest_command = device_commands.get(device_id)
        
        return JsonResponse({
            'status': 'success',
            'device': {
                'device_id': device.device_id,
                'name': device.name,
                'location': device.location,
                'is_active': device.is_active,
                'last_seen': device.last_seen.isoformat(),
                'uptime_hours': (timezone.now() - device.created_at).total_seconds() / 3600
            },
            'latest_readings': latest_readings,
            'latest_command': {
                'command_type': latest_command.command_type if latest_command else None,
                'parameters': latest_command.parameters if latest_command else None,
                'created_at': latest_command.created_at.isoformat() if latest_command else None,
                'executed': latest_command.executed if latest_command else False
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting device status: {e}")
        return JsonResponse({
            'status': 'error',
            'message': 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_plant_profiles(request):
    """
    Get all available plant profiles
    GET /api/plant-profiles
    """
    try:
        profiles_data = {}
        for name, profile in PLANT_PROFILES.items():
            profiles_data[name] = {
                'name': profile.name,
                'display_name': profile.display_name,
                'soil_moisture_min': profile.soil_moisture_min,
                'soil_moisture_max': profile.soil_moisture_max,
                'temperature_min': profile.temperature_min,
                'temperature_max': profile.temperature_max,
                'light_hours': profile.light_hours,
                'light_intensity': profile.light_intensity,
                'optimal_conditions': {
                    'soil_moisture': (profile.soil_moisture_min + profile.soil_moisture_max) / 2,
                    'temperature': (profile.temperature_min + profile.temperature_max) / 2,
                    'humidity': 65,
                    'light_hours': profile.light_hours
                }
            }
        
        return JsonResponse({
            'status': 'success',
            'profiles': profiles_data
        })
        
    except Exception as e:
        logger.error(f"Error getting plant profiles: {e}")
        return JsonResponse({
            'status': 'error',
            'message': 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_device_list(request):
    """
    Get list of all IoT devices
    GET /api/devices
    """
    try:
        devices_data = []
        for device_id, device in devices.items():
            # Get latest sensor readings
            device_readings_filtered = [
                r for r in sensor_readings if r.device_id == device_id
            ]
            
            # Calculate device health
            recent_readings = len([r for r in device_readings_filtered if r.timestamp >= timezone.now() - timedelta(hours=1)])
            is_healthy = recent_readings > 0
            
            devices_data.append({
                'device_id': device.device_id,
                'name': device.name,
                'location': device.location,
                'is_active': device.is_active,
                'is_healthy': is_healthy,
                'last_seen': device.last_seen.isoformat(),
                'recent_readings': recent_readings
            })
        
        return JsonResponse({
            'status': 'success',
            'devices': devices_data,
            'total_devices': len(devices_data)
        })
        
    except Exception as e:
        logger.error(f"Error getting device list: {e}")
        return JsonResponse({
            'status': 'error',
            'message': 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def emergency_stop(request):
    """
    Emergency stop - turn off all devices
    POST /api/emergency-stop
    """
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id', 'all')
        
        if device_id == 'all':
            # Stop all devices
            for dev_id in devices.keys():
                command = store_device_command(
                    device_id=dev_id,
                    command_type='emergency_stop',
                    parameters={'stop_all': True},
                    user=request.user
                )
        else:
            # Stop specific device
            command = store_device_command(
                device_id=device_id,
                command_type='emergency_stop',
                parameters={'stop_all': True},
                user=request.user
            )
        
        logger.warning(f"Emergency stop activated for {device_id} by {request.user}")
        
        return JsonResponse({
            'status': 'success',
            'message': 'Emergency stop activated',
            'device_id': device_id,
            'timestamp': timezone.now().isoformat()
        })
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in emergency stop: {e}")
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON data'
        }, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        logger.error(f"Error in emergency stop: {e}")
        return JsonResponse({
            'status': 'error',
            'message': 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def irrigation_dashboard(request):
    """
    Main dashboard view for Smart Irrigation System
    """
    return render(request, 'core/smart_irrigation_dashboard.html', {
        'page_title': 'Smart IoT Irrigation System',
        'devices': list(devices.values()),
        'plant_profiles': PLANT_PROFILES
    })
