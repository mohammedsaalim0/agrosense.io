from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db.models import Q, Avg, Max, Min
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
import json
import paho.mqtt.client as mqtt
from django.core.cache import cache
from datetime import datetime, timedelta

from .models import (
    CropEnvironment, IoTDevice, SensorReading, ActuatorState,
    IrrigationSchedule, ChamberControlLog, SystemAlert
)

# MQTT Configuration
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_USERNAME = "agrosense_user"
MQTT_PASSWORD = "secure_password"

class IoTChamberMQTTManager:
    """MQTT client for IoT Chamber communication"""
    
    def __init__(self):
        self.client = mqtt.Client()
        self.client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        
        # Start MQTT thread
        import threading
        self.mqtt_thread = threading.Thread(target=self.mqtt_loop, daemon=True)
        self.mqtt_thread.start()
    
    def mqtt_loop(self):
        try:
            self.client.connect(MQTT_BROKER, MQTT_PORT, 60)
            self.client.loop_forever()
        except Exception as e:
            print(f"MQTT Connection Error: {e}")
            import time
            time.sleep(5)
            self.mqtt_loop()
    
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("IoT Chamber MQTT Connected")
            # Subscribe to all device data topics
            client.subscribe("agrosense/chamber/+/data/#")
            client.subscribe("agrosense/chamber/+/status/#")
        else:
            print(f"MQTT Connection failed with code {rc}")
    
    def on_message(self, client, userdata, msg):
        try:
            topic_parts = msg.topic.split('/')
            if len(topic_parts) >= 4:
                device_id = topic_parts[2]
                message_type = topic_parts[3]
                sub_type = topic_parts[4] if len(topic_parts) > 4 else None
                
                data = json.loads(msg.payload.decode())
                self.process_device_data(device_id, message_type, sub_type, data)
        except Exception as e:
            print(f"MQTT Message Error: {e}")
    
    def on_disconnect(self, client, userdata, rc):
        print(f"MQTT Disconnected with code {rc}")
    
    def process_device_data(self, device_id, message_type, sub_type, data):
        """Process incoming data from IoT devices"""
        try:
            # Get or create device
            device, created = IoTDevice.objects.get_or_create(
                device_id=device_id,
                defaults={
                    'name': f"Device {device_id}",
                    'device_type': 'chamber',
                    'is_online': True,
                    'last_seen': timezone.now()
                }
            )
            
            if not created:
                device.is_online = True
                device.last_seen = timezone.now()
                device.save()
            
            # Process sensor data
            if message_type == 'sensors':
                SensorReading.objects.create(
                    device=device,
                    sensor_type=sub_type,
                    value=data.get('value'),
                    unit=data.get('unit', ''),
                    quality_score=data.get('quality', 100.0),
                    timestamp=timezone.now()
                )
            
            # Process actuator status
            elif message_type == 'status':
                ActuatorState.objects.update_or_create(
                    device=device,
                    actuator_type=sub_type,
                    defaults={
                        'is_active': data.get('is_active', False),
                        'power_level': data.get('power_level', 0),
                        'control_mode': data.get('control_mode', 'auto')
                    }
                )
            
            # Update cache for real-time access
            cache_key = f"chamber_{device_id}_{message_type}"
            cache.set(cache_key, data, timeout=300)  # 5 minutes
            
        except Exception as e:
            print(f"Data processing error: {e}")
    
    def send_command(self, device_id, command, data):
        """Send command to IoT device"""
        try:
            topic = f"agrosense/chamber/{device_id}/command/{command}"
            message = json.dumps(data)
            
            result = self.client.publish(topic, message, qos=1)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                # Log the command
                device = IoTDevice.objects.get(device_id=device_id)
                ChamberControlLog.objects.create(
                    device=device,
                    action_type='manual_control',
                    description=f"Sent {command} command",
                    target_actuator=command,
                    new_value=data,
                    source='web_dashboard'
                )
                return True
            else:
                print(f"MQTT Publish failed: {result.rc}")
                return False
        except Exception as e:
            print(f"Command sending error: {e}")
            return False

# Global MQTT manager instance
mqtt_manager = IoTChamberMQTTManager()

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def chamber_dashboard_api(request):
    """Get chamber dashboard data"""
    try:
        devices = IoTDevice.objects.filter(is_active=True)
        device_data = []
        
        for device in devices:
            # Get latest sensor readings
            latest_readings = {}
            for sensor_type in ['temperature', 'humidity', 'soil_moisture', 'light']:
                reading = SensorReading.objects.filter(
                    device=device, 
                    sensor_type=sensor_type
                ).order_by('-timestamp').first()
                
                if reading:
                    latest_readings[sensor_type] = {
                        'value': reading.value,
                        'unit': reading.unit,
                        'timestamp': reading.timestamp.isoformat(),
                        'quality': reading.quality_score
                    }
            
            # Get current actuator states
            actuator_states = {}
            for actuator in ActuatorState.objects.filter(device=device):
                actuator_states[actuator.actuator_type] = {
                    'is_active': actuator.is_active,
                    'power_level': actuator.power_level,
                    'control_mode': actuator.control_mode,
                    'last_changed': actuator.last_changed.isoformat()
                }
            
            # Get active alerts
            alerts = SystemAlert.objects.filter(
                device=device,
                is_resolved=False
            ).order_by('-created_at')[:5]
            
            device_data.append({
                'device_id': device.device_id,
                'name': device.name,
                'device_type': device.get_device_type_display(),
                'location': device.location,
                'is_online': device.is_online,
                'last_seen': device.last_seen.isoformat() if device.last_seen else None,
                'sensors': latest_readings,
                'actuators': actuator_states,
                'alerts': [
                    {
                        'id': alert.id,
                        'title': alert.title,
                        'severity': alert.severity,
                        'message': alert.message,
                        'created_at': alert.created_at.isoformat()
                    }
                    for alert in alerts
                ]
            })
        
        return Response({
            'status': 'success',
            'data': device_data,
            'timestamp': timezone.now().isoformat()
        })
        
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def crop_environments_api(request):
    """Get available crop environments"""
    try:
        crops = CropEnvironment.objects.filter(is_active=True)
        
        crop_data = []
        for crop in crops:
            crop_data.append({
                'id': crop.id,
                'name': crop.name,
                'scientific_name': crop.scientific_name,
                'description': crop.description,
                'optimal_temperature': crop.optimal_temperature,
                'temperature_tolerance': crop.temperature_tolerance,
                'optimal_humidity': crop.optimal_humidity,
                'humidity_tolerance': crop.humidity_tolerance,
                'optimal_moisture': crop.optimal_moisture,
                'moisture_tolerance': crop.moisture_tolerance,
                'light_hours': crop.light_hours,
                'light_intensity': crop.light_intensity,
                'growth_stage_days': crop.growth_stage_days,
                'water_consumption': crop.water_consumption
            })
        
        return Response({
            'status': 'success',
            'data': crop_data
        })
        
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@csrf_exempt
def select_crop_environment_api(request):
    """Select and apply crop environment to chamber"""
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')
        crop_id = data.get('crop_id')
        
        device = get_object_or_404(IoTDevice, device_id=device_id)
        crop = get_object_or_404(CropEnvironment, id=crop_id)
        
        # Send crop environment to device
        environment_data = {
            'crop': crop.name,
            'temperature': crop.optimal_temperature,
            'humidity': crop.optimal_humidity,
            'moisture': crop.optimal_moisture,
            'light_hours': crop.light_hours,
            'light_intensity': crop.light_intensity,
            'tolerances': {
                'temperature': crop.temperature_tolerance,
                'humidity': crop.humidity_tolerance,
                'moisture': crop.moisture_tolerance
            }
        }
        
        success = mqtt_manager.send_command(device_id, 'set_environment', environment_data)
        
        if success:
            # Update device configuration
            device.configuration.update({
                'active_crop': crop.name,
                'crop_environment_id': crop.id,
                'environment_set_at': timezone.now().isoformat()
            })
            device.save()
            
            # Log the action
            ChamberControlLog.objects.create(
                device=device,
                action_type='manual_control',
                description=f"Set environment for {crop.name}",
                new_value=environment_data,
                user=request.user,
                source='web_dashboard'
            )
            
            return Response({
                'status': 'success',
                'message': f'Environment set for {crop.name}',
                'environment': environment_data
            })
        else:
            return Response({
                'status': 'error',
                'message': 'Failed to send environment command to device'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except json.JSONDecodeError:
        return Response({
            'status': 'error',
            'message': 'Invalid JSON data'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@csrf_exempt
def manual_control_api(request):
    """Manual control of chamber actuators"""
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')
        actuator_type = data.get('actuator_type')
        action = data.get('action')  # 'on', 'off', 'toggle'
        power_level = data.get('power_level', 100)
        
        device = get_object_or_404(IoTDevice, device_id=device_id)
        
        # Determine new state
        current_state = ActuatorState.objects.filter(
            device=device, 
            actuator_type=actuator_type
        ).first()
        
        if action == 'toggle':
            new_state = not (current_state.is_active if current_state else False)
        elif action == 'on':
            new_state = True
        elif action == 'off':
            new_state = False
        else:
            return Response({
                'status': 'error',
                'message': 'Invalid action. Use: on, off, or toggle'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Send command to device
        command_data = {
            'actuator': actuator_type,
            'is_active': new_state,
            'power_level': power_level,
            'control_mode': 'manual'
        }
        
        success = mqtt_manager.send_command(device_id, 'control_actuator', command_data)
        
        if success:
            # Update local state
            ActuatorState.objects.update_or_create(
                device=device,
                actuator_type=actuator_type,
                defaults={
                    'is_active': new_state,
                    'power_level': power_level,
                    'control_mode': 'manual'
                }
            )
            
            # Log the action
            ChamberControlLog.objects.create(
                device=device,
                action_type='manual_control',
                description=f"Manual {actuator_type} {action}",
                target_actuator=actuator_type,
                old_value={'is_active': current_state.is_active} if current_state else None,
                new_value={'is_active': new_state, 'power_level': power_level},
                user=request.user,
                source='web_dashboard'
            )
            
            return Response({
                'status': 'success',
                'message': f'{actuator_type} turned {"on" if new_state else "off"}',
                'actuator_state': {
                    'actuator_type': actuator_type,
                    'is_active': new_state,
                    'power_level': power_level
                }
            })
        else:
            return Response({
                'status': 'error',
                'message': 'Failed to send control command to device'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except json.JSONDecodeError:
        return Response({
            'status': 'error',
            'message': 'Invalid JSON data'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sensor_history_api(request):
    """Get historical sensor data"""
    try:
        device_id = request.GET.get('device_id')
        sensor_type = request.GET.get('sensor_type', 'temperature')
        hours = int(request.GET.get('hours', 24))
        
        device = get_object_or_404(IoTDevice, device_id=device_id)
        
        # Get data for specified time period
        start_time = timezone.now() - timedelta(hours=hours)
        readings = SensorReading.objects.filter(
            device=device,
            sensor_type=sensor_type,
            timestamp__gte=start_time
        ).order_by('timestamp')
        
        # Aggregate data by hour for better performance
        aggregated_data = {}
        for reading in readings:
            hour_key = reading.timestamp.strftime('%Y-%m-%d %H:00')
            if hour_key not in aggregated_data:
                aggregated_data[hour_key] = {
                    'timestamp': hour_key,
                    'values': [],
                    'unit': reading.unit
                }
            aggregated_data[hour_key]['values'].append(reading.value)
        
        # Calculate statistics for each hour
        history_data = []
        for hour_key, data in aggregated_data.items():
            values = data['values']
            history_data.append({
                'timestamp': data['timestamp'],
                'value': sum(values) / len(values),  # Average
                'min': min(values),
                'max': max(values),
                'count': len(values),
                'unit': data['unit']
            })
        
        return Response({
            'status': 'success',
            'data': history_data,
            'sensor_type': sensor_type,
            'device_id': device_id,
            'period_hours': hours
        })
        
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@csrf_exempt
def irrigation_schedule_api(request):
    """Create or update irrigation schedule"""
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')
        
        device = get_object_or_404(IoTDevice, device_id=device_id)
        
        if 'schedule_id' in data:
            # Update existing schedule
            schedule = get_object_or_404(IrrigationSchedule, id=data['schedule_id'], device=device)
            schedule.start_time = data.get('start_time', schedule.start_time)
            schedule.duration_minutes = data.get('duration_minutes', schedule.duration_minutes)
            schedule.days_of_week = data.get('days_of_week', schedule.days_of_week)
            schedule.moisture_threshold = data.get('moisture_threshold', schedule.moisture_threshold)
            schedule.skip_rain = data.get('skip_rain', schedule.skip_rain)
            schedule.is_active = data.get('is_active', schedule.is_active)
            schedule.save()
            
            message = 'Irrigation schedule updated'
        else:
            # Create new schedule
            schedule = IrrigationSchedule.objects.create(
                device=device,
                name=data.get('name'),
                start_time=data.get('start_time'),
                duration_minutes=data.get('duration_minutes'),
                days_of_week=data.get('days_of_week', [1,2,3,4,5]),
                moisture_threshold=data.get('moisture_threshold'),
                skip_rain=data.get('skip_rain', True),
                is_active=data.get('is_active', True)
            )
            message = 'Irrigation schedule created'
        
        # Send schedule to device
        schedule_data = {
            'schedule_id': schedule.id,
            'name': schedule.name,
            'start_time': schedule.start_time.strftime('%H:%M'),
            'duration_minutes': schedule.duration_minutes,
            'days_of_week': schedule.days_of_week,
            'moisture_threshold': schedule.moisture_threshold,
            'skip_rain': schedule.skip_rain,
            'is_active': schedule.is_active
        }
        
        mqtt_manager.send_command(device_id, 'set_schedule', schedule_data)
        
        return Response({
            'status': 'success',
            'message': message,
            'schedule': {
                'id': schedule.id,
                'name': schedule.name,
                'start_time': schedule.start_time.strftime('%H:%M'),
                'duration_minutes': schedule.duration_minutes,
                'days_of_week': schedule.days_of_week,
                'moisture_threshold': schedule.moisture_threshold,
                'skip_rain': schedule.skip_rain,
                'is_active': schedule.is_active
            }
        })
        
    except json.JSONDecodeError:
        return Response({
            'status': 'error',
            'message': 'Invalid JSON data'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def system_alerts_api(request):
    """Get system alerts"""
    try:
        device_id = request.GET.get('device_id')
        severity = request.GET.get('severity')
        resolved = request.GET.get('resolved', 'false').lower() == 'true'
        
        alerts_query = SystemAlert.objects.all()
        
        if device_id:
            alerts_query = alerts_query.filter(device__device_id=device_id)
        
        if severity:
            alerts_query = alerts_query.filter(severity=severity)
        
        if not resolved:
            alerts_query = alerts_query.filter(is_resolved=False)
        
        alerts = alerts_query.order_by('-created_at')[:50]
        
        alert_data = []
        for alert in alerts:
            alert_data.append({
                'id': alert.id,
                'device_id': alert.device.device_id if alert.device else None,
                'device_name': alert.device.name if alert.device else 'System',
                'alert_type': alert.alert_type,
                'severity': alert.severity,
                'title': alert.title,
                'message': alert.message,
                'details': alert.details,
                'is_acknowledged': alert.is_acknowledged,
                'acknowledged_by': alert.acknowledged_by.username if alert.acknowledged_by else None,
                'acknowledged_at': alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
                'is_resolved': alert.is_resolved,
                'resolved_at': alert.resolved_at.isoformat() if alert.resolved_at else None,
                'created_at': alert.created_at.isoformat()
            })
        
        return Response({
            'status': 'success',
            'data': alert_data,
            'count': len(alert_data)
        })
        
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def chamber_control_logs_api(request):
    """Get control action logs"""
    try:
        device_id = request.GET.get('device_id')
        action_type = request.GET.get('action_type')
        limit = int(request.GET.get('limit', 100))
        
        logs_query = ChamberControlLog.objects.all()
        
        if device_id:
            logs_query = logs_query.filter(device__device_id=device_id)
        
        if action_type:
            logs_query = logs_query.filter(action_type=action_type)
        
        logs = logs_query.order_by('-timestamp')[:limit]
        
        log_data = []
        for log in logs:
            log_data.append({
                'id': log.id,
                'device_id': log.device.device_id,
                'device_name': log.device.name,
                'action_type': log.action_type,
                'description': log.description,
                'target_actuator': log.target_actuator,
                'old_value': log.old_value,
                'new_value': log.new_value,
                'user': log.user.username if log.user else 'System',
                'source': log.source,
                'success': log.success,
                'error_message': log.error_message,
                'timestamp': log.timestamp.isoformat()
            })
        
        return Response({
            'status': 'success',
            'data': log_data,
            'count': len(log_data)
        })
        
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Web views for rendering templates
def smart_chamber_dashboard(request):
    """Main Smart IoT Chamber dashboard"""
    if not request.user.is_authenticated:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    
    devices = IoTDevice.objects.filter(is_active=True)
    crops = CropEnvironment.objects.filter(is_active=True)
    
    context = {
        'devices': devices,
        'crops': crops,
        'page_title': 'Smart IoT Chamber Control'
    }
    
    return render(request, 'core/smart_chamber_dashboard.html', context)
