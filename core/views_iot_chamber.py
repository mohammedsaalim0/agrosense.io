"""
Smart IoT Chamber Django Views and APIs
Production-ready REST API endpoints for chamber control and monitoring
"""

import json
from datetime import datetime, timedelta
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db.models import Q, Avg, Max, Min
from django.contrib.auth.decorators import login_required
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.response import Response

from .models import (
    IoTDevice, CropEnvironment, SensorReading, ActuatorState,
    IrrigationSchedule, ChamberControlLog, SystemAlert,
    DeviceConfiguration
)
from .mqtt_service import mqtt_service


@login_required
def smart_chamber_dashboard(request):
    """
    Main Smart IoT Chamber dashboard view
    """
    # Get active devices
    devices = IoTDevice.objects.filter(is_active=True).order_by('name')
    
    # Get crop environments
    crop_environments = CropEnvironment.objects.filter(is_active=True).order_by('name')
    
    # Get recent alerts
    recent_alerts = SystemAlert.objects.filter(
        is_resolved=False
    ).order_by('-created_at')[:10]
    
    context = {
        'devices': devices,
        'crop_environments': crop_environments,
        'recent_alerts': recent_alerts,
        'page_title': 'Smart IoT Chamber',
    }
    
    return render(request, 'core/smart_chamber_dashboard.html', context)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def chamber_dashboard_api(request):
    """
    API endpoint for chamber dashboard data
    Returns comprehensive chamber status and sensor data
    """
    try:
        device_id = request.GET.get('device_id')
        
        if device_id:
            # Get specific device data
            device = get_object_or_404(IoTDevice, device_id=device_id)
            devices = [device]
        else:
            # Get all active devices
            devices = IoTDevice.objects.filter(is_active=True, is_online=True)
        
        dashboard_data = []
        
        for device in devices:
            # Get latest sensor readings
            latest_readings = SensorReading.get_latest_readings(
                device.device_id,
                ['temperature', 'humidity', 'soil_moisture', 'light']
            )
            
            # Get actuator states
            actuator_states = {}
            for actuator in device.actuator_states.all():
                actuator_states[actuator.actuator_type] = {
                    'is_active': actuator.is_active,
                    'power_level': actuator.power_level,
                    'last_changed': actuator.last_changed.isoformat()
                }
            
            # Get device configuration
            try:
                config = device.configuration_profile
                device_config = {
                    'max_pump_runtime': config.max_pump_runtime,
                    'min_moisture_threshold': config.min_moisture_threshold,
                    'max_temperature_limit': config.max_temperature_limit,
                    'min_temperature_limit': config.min_temperature_limit
                }
            except DeviceConfiguration.DoesNotExist:
                device_config = {}
            
            # Get active crop environment if set
            active_crop = None
            if device.configuration and 'active_crop' in device.configuration:
                try:
                    crop_id = device.configuration['active_crop']
                    active_crop = CropEnvironment.objects.get(id=crop_id)
                except (CropEnvironment.DoesNotExist, ValueError):
                    pass
            
            # Get recent alerts for this device
            recent_alerts = SystemAlert.objects.filter(
                device=device,
                is_resolved=False
            ).order_by('-created_at')[:5]
            
            device_data = {
                'device_id': device.device_id,
                'name': device.name,
                'device_type': device.get_device_type_display(),
                'status': device.status,
                'is_online': device.is_online,
                'last_seen': device.last_seen.isoformat() if device.last_seen else None,
                'location': device.location,
                'sensor_readings': latest_readings,
                'actuator_states': actuator_states,
                'configuration': device_config,
                'active_crop': {
                    'id': active_crop.id,
                    'name': active_crop.name,
                    'optimal_temperature': active_crop.optimal_temperature,
                    'optimal_humidity': active_crop.optimal_humidity,
                    'optimal_soil_moisture': active_crop.optimal_soil_moisture
                } if active_crop else None,
                'recent_alerts': [
                    {
                        'id': alert.id,
                        'type': alert.alert_type,
                        'severity': alert.severity,
                        'title': alert.title,
                        'message': alert.message,
                        'created_at': alert.created_at.isoformat()
                    }
                    for alert in recent_alerts
                ]
            }
            
            dashboard_data.append(device_data)
        
        return Response({
            'status': 'success',
            'data': dashboard_data,
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
    """
    API endpoint for available crop environments
    """
    try:
        crops = CropEnvironment.objects.filter(is_active=True).order_by('name')
        
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
                'optimal_soil_moisture': crop.optimal_soil_moisture,
                'moisture_tolerance': crop.moisture_tolerance,
                'light_hours': crop.light_hours,
                'light_intensity': crop.light_intensity,
                'water_consumption': crop.water_consumption,
                'growth_stages': crop.growth_stages
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
    """
    API endpoint to select and apply crop environment to chamber
    """
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')
        crop_id = data.get('crop_id')
        
        device = get_object_or_404(IoTDevice, device_id=device_id)
        crop = get_object_or_404(CropEnvironment, id=crop_id)
        
        # Update device configuration
        device.configuration.update({
            'active_crop': crop.id,
            'crop_environment_id': crop.id,
            'environment_set_at': timezone.now().isoformat()
        })
        device.save()
        
        # Publish environment settings to device via MQTT
        success = mqtt_service.publish_environment_settings(device_id, crop)
        
        # Log the action
        ChamberControlLog.objects.create(
            device=device,
            action_type='manual_control',
            description=f"Set environment for {crop.name}",
            target_actuator='environment',
            old_value=device.configuration.get('active_crop'),
            new_value=crop.id,
            user=request.user,
            source='web_dashboard',
            success=success
        )
        
        return Response({
            'status': 'success',
            'message': f'Environment set for {crop.name}',
            'command_sent': success
        })
        
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@csrf_exempt
def manual_control_api(request):
    """
    API endpoint for manual actuator control
    """
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')
        actuator_type = data.get('actuator_type')
        action = data.get('action')  # 'on', 'off', 'toggle'
        power_level = data.get('power_level', 100)
        
        device = get_object_or_404(IoTDevice, device_id=device_id)
        
        # Validate actuator type
        valid_actuators = [choice[0] for choice in ActuatorState.ACTUATOR_TYPES]
        if actuator_type not in valid_actuators:
            return Response({
                'status': 'error',
                'message': f'Invalid actuator type: {actuator_type}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get current actuator state
        current_state = ActuatorState.objects.filter(
            device=device, 
            actuator_type=actuator_type
        ).first()
        
        # Determine new state
        if action == 'toggle':
            new_state = not (current_state.is_active if current_state else False)
        else:
            new_state = action == 'on'
        
        # Update local database
        ActuatorState.objects.update_or_create(
            device=device,
            actuator_type=actuator_type,
            defaults={
                'is_active': new_state,
                'power_level': power_level if new_state else 0,
                'control_mode': 'manual',
                'last_changed': timezone.now()
            }
        )
        
        # Publish command to device via MQTT
        success = mqtt_service.publish_manual_control(
            device_id, actuator_type, 'on' if new_state else 'off', power_level
        )
        
        # Log the action
        ChamberControlLog.objects.create(
            device=device,
            action_type='manual_control',
            description=f"Manual {actuator_type} {'on' if new_state else 'off'}",
            target_actuator=actuator_type,
            old_value={'is_active': current_state.is_active} if current_state else None,
            new_value={'is_active': new_state, 'power_level': power_level},
            user=request.user,
            source='web_dashboard',
            success=success
        )
        
        return Response({
            'status': 'success',
            'message': f'{actuator_type} turned {"on" if new_state else "off"}',
            'command_sent': success,
            'actuator_state': {
                'is_active': new_state,
                'power_level': power_level
            }
        })
        
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sensor_history_api(request):
    """
    API endpoint for historical sensor data
    """
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
        
        # Format data for Chart.js
        history_data = []
        for reading in readings:
            history_data.append({
                'timestamp': reading.timestamp.isoformat(),
                'value': reading.value,
                'quality_score': reading.quality_score
            })
        
        return Response({
            'status': 'success',
            'data': history_data,
            'sensor_type': sensor_type,
            'time_range_hours': hours,
            'data_points': len(history_data)
        })
        
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def system_alerts_api(request):
    """
    API endpoint for system alerts
    """
    try:
        device_id = request.GET.get('device_id')
        severity = request.GET.get('severity')
        resolved = request.GET.get('resolved', 'false').lower() == 'true'
        limit = int(request.GET.get('limit', 50))
        
        alerts_query = SystemAlert.objects.all()
        
        if device_id:
            alerts_query = alerts_query.filter(device__device_id=device_id)
        
        if severity:
            alerts_query = alerts_query.filter(severity=severity)
        
        if not resolved:
            alerts_query = alerts_query.filter(is_resolved=False)
        
        alerts = alerts_query.order_by('-created_at')[:limit]
        
        alerts_data = []
        for alert in alerts:
            alerts_data.append({
                'id': alert.id,
                'device_id': alert.device.device_id if alert.device else None,
                'device_name': alert.device.name if alert.device else None,
                'alert_type': alert.alert_type,
                'severity': alert.severity,
                'title': alert.title,
                'message': alert.message,
                'details': alert.details,
                'is_acknowledged': alert.is_acknowledged,
                'acknowledged_by': alert.acknowledged_by.username if alert.acknowledged_by else None,
                'acknowledged_at': alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
                'is_resolved': alert.is_resolved,
                'resolved_by': alert.resolved_by.username if alert.resolved_by else None,
                'resolved_at': alert.resolved_at.isoformat() if alert.resolved_at else None,
                'created_at': alert.created_at.isoformat()
            })
        
        return Response({
            'status': 'success',
            'data': alerts_data,
            'total_count': len(alerts_data)
        })
        
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@csrf_exempt
def acknowledge_alert_api(request):
    """
    API endpoint to acknowledge system alert
    """
    try:
        data = json.loads(request.body)
        alert_id = data.get('alert_id')
        
        alert = get_object_or_404(SystemAlert, id=alert_id)
        alert.acknowledge(request.user)
        
        return Response({
            'status': 'success',
            'message': 'Alert acknowledged successfully',
            'acknowledged_at': alert.acknowledged_at.isoformat()
        })
        
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@csrf_exempt
def resolve_alert_api(request):
    """
    API endpoint to resolve system alert
    """
    try:
        data = json.loads(request.body)
        alert_id = data.get('alert_id')
        notes = data.get('notes', '')
        
        alert = get_object_or_404(SystemAlert, id=alert_id)
        alert.resolve(request.user, notes)
        
        return Response({
            'status': 'success',
            'message': 'Alert resolved successfully',
            'resolved_at': alert.resolved_at.isoformat()
        })
        
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def control_logs_api(request):
    """
    API endpoint for chamber control logs
    """
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
        
        logs_data = []
        for log in logs:
            logs_data.append({
                'id': log.id,
                'device_id': log.device.device_id,
                'device_name': log.device.name,
                'action_type': log.action_type,
                'description': log.description,
                'target_actuator': log.target_actuator,
                'old_value': log.old_value,
                'new_value': log.new_value,
                'success': log.success,
                'error_message': log.error_message,
                'source': log.source,
                'user': log.user.username if log.user else None,
                'execution_time_ms': log.execution_time_ms,
                'timestamp': log.timestamp.isoformat()
            })
        
        return Response({
            'status': 'success',
            'data': logs_data,
            'total_count': len(logs_data)
        })
        
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def irrigation_schedule_api(request):
    """
    API endpoint for irrigation schedules (GET for list, POST for create/update)
    """
    try:
        if request.method == 'GET':
            device_id = request.GET.get('device_id')
            
            schedules_query = IrrigationSchedule.objects.all()
            
            if device_id:
                schedules_query = schedules_query.filter(device__device_id=device_id)
            
            schedules = schedules_query.order_by('start_time')
            
            schedules_data = []
            for schedule in schedules:
                schedules_data.append({
                    'id': schedule.id,
                    'device_id': schedule.device.device_id,
                    'device_name': schedule.device.name,
                    'name': schedule.name,
                    'start_time': schedule.start_time.strftime('%H:%M'),
                    'duration_minutes': schedule.duration_minutes,
                    'days_of_week': schedule.days_of_week,
                    'moisture_threshold': schedule.moisture_threshold,
                    'skip_rain': schedule.skip_rain,
                    'is_active': schedule.is_active,
                    'last_run': schedule.last_run.isoformat() if schedule.last_run else None,
                    'next_run': schedule.next_run.isoformat() if schedule.next_run else None
                })
            
            return Response({
                'status': 'success',
                'data': schedules_data
            })
        
        elif request.method == 'POST':
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
            else:
                # Create new schedule
                schedule = IrrigationSchedule.objects.create(
                    device=device,
                    name=data.get('name', 'Irrigation Schedule'),
                    start_time=data.get('start_time', '06:00'),
                    duration_minutes=data.get('duration_minutes', 15),
                    days_of_week=data.get('days_of_week', [1, 2, 3, 4, 5, 6, 7]),
                    moisture_threshold=data.get('moisture_threshold', 60.0),
                    skip_rain=data.get('skip_rain', True),
                    is_active=data.get('is_active', True),
                    created_by=request.user
                )
            
            schedule.save()
            
            return Response({
                'status': 'success',
                'message': 'Irrigation schedule saved successfully',
                'schedule_id': schedule.id
            })
        
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@csrf_exempt
def emergency_stop_api(request):
    """
    API endpoint for emergency stop
    """
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')
        
        device = get_object_or_404(IoTDevice, device_id=device_id)
        
        # Publish emergency stop command via MQTT
        success = mqtt_service.publish_emergency_stop(device_id)
        
        # Log the emergency stop
        ChamberControlLog.objects.create(
            device=device,
            action_type='emergency_stop',
            description='Emergency stop activated',
            user=request.user,
            source='web_dashboard',
            success=success
        )
        
        # Create system alert
        SystemAlert.objects.create(
            device=device,
            alert_type='system_error',
            severity='critical',
            title='Emergency Stop Activated',
            message=f'Emergency stop was activated for {device.name}',
            details={
                'activated_by': request.user.username,
                'timestamp': timezone.now().isoformat()
            }
        )
        
        return Response({
            'status': 'success',
            'message': 'Emergency stop command sent',
            'command_sent': success
        })
        
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mqtt_status_api(request):
    """
    API endpoint to check MQTT service status
    """
    try:
        stats = mqtt_service.get_statistics()
        
        return Response({
            'status': 'success',
            'data': stats
        })
        
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@csrf_exempt
def water_now_api(request):
    """
    API endpoint for immediate irrigation (water now)
    """
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')
        duration = data.get('duration', 30)  # Default 30 seconds
        
        device = get_object_or_404(IoTDevice, device_id=device_id)
        
        # Get device configuration for safety limits
        try:
            config = device.configuration_profile
            max_runtime = config.max_pump_runtime
        except DeviceConfiguration.DoesNotExist:
            max_runtime = 300  # 5 minutes default
        
        # Validate duration
        if duration > max_runtime:
            return Response({
                'status': 'error',
                'message': f'Duration exceeds maximum limit of {max_runtime} seconds'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Publish water now command via MQTT
        payload = {
            'command': 'water_now',
            'duration_seconds': duration,
            'timestamp': timezone.now().isoformat()
        }
        
        success = mqtt_service.publish_command(device_id, 'irrigation', payload)
        
        # Log the action
        ChamberControlLog.objects.create(
            device=device,
            action_type='manual_control',
            description=f'Immediate irrigation for {duration} seconds',
            target_actuator='water_pump',
            new_value={'duration': duration},
            user=request.user,
            source='web_dashboard',
            success=success
        )
        
        return Response({
            'status': 'success',
            'message': f'Irrigation started for {duration} seconds',
            'command_sent': success
        })
        
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
