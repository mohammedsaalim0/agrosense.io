"""
Django MQTT Service for Smart IoT Chamber
Production-ready MQTT client with bidirectional communication
"""

import json
import time
import threading
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

import paho.mqtt.client as mqtt
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction

from .models import (
    IoTDevice, SensorReading, ActuatorState, 
    ChamberControlLog, SystemAlert, CropEnvironment,
    DeviceConfiguration
)

# Configure logging
logger = logging.getLogger(__name__)


class MQTTService:
    """
    Production-ready MQTT service for Smart IoT Chamber
    Handles bidirectional communication with ESP32 devices
    """
    
    def __init__(self):
        # MQTT Configuration
        self.broker_host = getattr(settings, 'MQTT_BROKER_HOST', 'broker.hivemq.com')
        self.broker_port = getattr(settings, 'MQTT_BROKER_PORT', 8883)
        self.broker_username = getattr(settings, 'MQTT_USERNAME', '')
        self.broker_password = getattr(settings, 'MQTT_PASSWORD', '')
        self.use_tls = getattr(settings, 'MQTT_USE_TLS', True)
        
        # Client configuration
        self.client_id = f"agrosense_backend_{int(time.time())}"
        self.client = None
        self.is_connected = False
        self.reconnect_delay = 5
        self.max_reconnect_delay = 60
        
        # Topic structure
        self.base_topic = "agrosense/chamber"
        self.command_topics = f"{self.base_topic}/+/command/+"
        self.data_topics = f"{self.base_topic}/+/data/+"
        self.alert_topics = f"{self.base_topic}/+/alerts/+"
        
        # Device tracking
        self.active_devices = set()
        self.last_heartbeat = {}
        
        # Statistics
        self.stats = {
            'messages_received': 0,
            'messages_sent': 0,
            'connection_attempts': 0,
            'last_connection': None,
            'uptime_start': time.time()
        }
    
    def setup_client(self):
        """Setup MQTT client with callbacks"""
        self.client = mqtt.Client(
            client_id=self.client_id,
            clean_session=True,
            protocol=mqtt.MQTTv311
        )
        
        # Set callbacks
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        self.client.on_publish = self._on_publish
        self.client.on_subscribe = self._on_subscribe
        
        # Set authentication if provided
        if self.broker_username and self.broker_password:
            self.client.username_pw_set(self.broker_username, self.broker_password)
        
        # Configure TLS if enabled
        if self.use_tls:
            self.client.tls_set()
            self.client.tls_insecure_set(False)  # Enforce certificate verification
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback for MQTT connection"""
        if rc == 0:
            self.is_connected = True
            self.stats['last_connection'] = timezone.now()
            logger.info(f"Connected to MQTT broker: {self.broker_host}:{self.broker_port}")
            
            # Subscribe to all relevant topics
            self._subscribe_to_topics()
            
            # Publish service status
            self._publish_service_status("online")
            
        else:
            self.is_connected = False
            logger.error(f"Failed to connect to MQTT broker. Return code: {rc}")
            self.stats['connection_attempts'] += 1
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback for MQTT disconnection"""
        self.is_connected = False
        logger.warning(f"Disconnected from MQTT broker. Return code: {rc}")
        
        # Mark all devices as offline after timeout
        self._mark_devices_offline()
    
    def _on_message(self, client, userdata, msg):
        """Callback for incoming MQTT messages"""
        try:
            self.stats['messages_received'] += 1
            
            # Parse topic
            topic_parts = msg.topic.split('/')
            if len(topic_parts) < 4:
                logger.warning(f"Invalid topic format: {msg.topic}")
                return
            
            device_id = topic_parts[2]
            message_type = topic_parts[3]
            data_type = topic_parts[4] if len(topic_parts) > 4 else None
            
            # Parse payload
            try:
                payload = json.loads(msg.payload.decode('utf-8'))
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON payload from {device_id}: {e}")
                return
            
            # Route message based on type
            if message_type == "data":
                self._handle_data_message(device_id, data_type, payload)
            elif message_type == "command":
                self._handle_command_response(device_id, data_type, payload)
            elif message_type == "alerts":
                self._handle_alert_message(device_id, payload)
            elif message_type == "status":
                self._handle_status_message(device_id, payload)
            else:
                logger.warning(f"Unknown message type: {message_type}")
                
        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")
    
    def _on_publish(self, client, userdata, mid):
        """Callback for published messages"""
        self.stats['messages_sent'] += 1
        logger.debug(f"Message published with ID: {mid}")
    
    def _on_subscribe(self, client, userdata, mid, granted_qos):
        """Callback for subscription"""
        logger.info(f"Subscribed with QoS: {granted_qos}")
    
    def _subscribe_to_topics(self):
        """Subscribe to all relevant topics"""
        topics = [
            (self.data_topics, 1),  # Sensor data
            (self.alert_topics, 1),  # Device alerts
            (f"{self.base_topic}/+/status", 1),  # Device status
        ]
        
        for topic, qos in topics:
            result, mid = self.client.subscribe(topic, qos)
            if result == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"Subscribed to: {topic}")
            else:
                logger.error(f"Failed to subscribe to: {topic}")
    
    def _handle_data_message(self, device_id: str, data_type: str, payload: Dict[str, Any]):
        """Handle sensor data messages"""
        try:
            # Get or create device
            device = self._get_or_create_device(device_id)
            
            # Update device heartbeat
            device.update_heartbeat()
            self.last_heartbeat[device_id] = timezone.now()
            self.active_devices.add(device_id)
            
            if data_type == "sensors":
                self._process_sensor_data(device, payload.get('data', {}))
            elif data_type == "actuators":
                self._process_actuator_data(device, payload.get('actuators', {}))
            else:
                logger.warning(f"Unknown data type: {data_type}")
                
        except Exception as e:
            logger.error(f"Error handling data message from {device_id}: {e}")
    
    def _process_sensor_data(self, device: IoTDevice, sensor_data: Dict[str, Any]):
        """Process sensor readings and store in database"""
        timestamp = timezone.now()
        
        with transaction.atomic():
            for sensor_type, value in sensor_data.items():
                if sensor_type in ['temperature', 'humidity', 'soil_moisture', 'light', 'ph', 'ec', 'co2', 'pressure']:
                    # Get unit for sensor type
                    unit = self._get_sensor_unit(sensor_type)
                    
                    # Create sensor reading
                    SensorReading.objects.create(
                        device=device,
                        sensor_type=sensor_type,
                        value=float(value),
                        unit=unit,
                        quality_score=0.95,  # Default quality score
                        timestamp=timestamp
                    )
                    
                    # Check for alerts
                    self._check_sensor_alerts(device, sensor_type, float(value))
    
    def _process_actuator_data(self, device: IoTDevice, actuator_data: Dict[str, Any]):
        """Process actuator state updates"""
        with transaction.atomic():
            for actuator_type, state in actuator_data.items():
                if isinstance(state, dict):
                    is_active = state.get('is_active', False)
                    power_level = state.get('power_level', 100)
                else:
                    is_active = bool(state)
                    power_level = 100 if is_active else 0
                
                # Update actuator state
                ActuatorState.objects.update_or_create(
                    device=device,
                    actuator_type=actuator_type,
                    defaults={
                        'is_active': is_active,
                        'power_level': power_level,
                        'last_changed': timezone.now()
                    }
                )
    
    def _handle_alert_message(self, device_id: str, payload: Dict[str, Any]):
        """Handle alert messages from devices"""
        try:
            device = IoTDevice.objects.get(device_id=device_id)
            
            SystemAlert.objects.create(
                device=device,
                alert_type=payload.get('alert_type', 'device_alert'),
                severity=payload.get('severity', 'warning'),
                title=payload.get('title', 'Device Alert'),
                message=payload.get('message', ''),
                details=payload.get('details', {}),
                notification_sent=False
            )
            
            logger.info(f"Alert received from {device_id}: {payload.get('title')}")
            
        except IoTDevice.DoesNotExist:
            logger.warning(f"Alert from unknown device: {device_id}")
    
    def _handle_status_message(self, device_id: str, payload: Dict[str, Any]):
        """Handle device status messages"""
        try:
            device = IoTDevice.objects.get(device_id=device_id)
            
            # Update device status
            device.is_online = payload.get('online', False)
            device.status = payload.get('status', 'online')
            device.last_seen = timezone.now()
            device.save()
            
            # Update heartbeat
            self.last_heartbeat[device_id] = timezone.now()
            self.active_devices.add(device_id)
            
        except IoTDevice.DoesNotExist:
            logger.warning(f"Status from unknown device: {device_id}")
    
    def _handle_command_response(self, device_id: str, command_type: str, payload: Dict[str, Any]):
        """Handle responses to command messages"""
        try:
            device = IoTDevice.objects.get(device_id=device_id)
            
            # Log command response
            ChamberControlLog.objects.create(
                device=device,
                action_type='manual_control',
                description=f"Command response: {command_type}",
                new_value=payload,
                success=payload.get('success', True),
                error_message=payload.get('error', ''),
                source='mqtt_command',
                timestamp=timezone.now()
            )
            
        except IoTDevice.DoesNotExist:
            logger.warning(f"Command response from unknown device: {device_id}")
    
    def _check_sensor_alerts(self, device: IoTDevice, sensor_type: str, value: float):
        """Check sensor values against thresholds and create alerts"""
        try:
            # Get device configuration
            config = DeviceConfiguration.objects.get(device=device)
            
            # Check different sensor types
            if sensor_type == 'temperature':
                if value > config.max_temperature_limit:
                    self._create_alert(device, 'temperature_high', 'error', 
                                     'High Temperature Alert', f'Temperature is {value}°C')
                elif value < config.min_temperature_limit:
                    self._create_alert(device, 'temperature_low', 'error', 
                                     'Low Temperature Alert', f'Temperature is {value}°C')
            
            elif sensor_type == 'soil_moisture':
                if value < config.min_moisture_threshold:
                    self._create_alert(device, 'moisture_low', 'warning', 
                                     'Low Soil Moisture', f'Soil moisture is {value}%')
            
        except DeviceConfiguration.DoesNotExist:
            # Use default thresholds if no configuration exists
            if sensor_type == 'temperature' and (value > 40 or value < 5):
                self._create_alert(device, 'temperature_extreme', 'critical', 
                                 'Extreme Temperature', f'Temperature is {value}°C')
            elif sensor_type == 'soil_moisture' and value < 20:
                self._create_alert(device, 'moisture_low', 'warning', 
                                 'Low Soil Moisture', f'Soil moisture is {value}%')
    
    def _create_alert(self, device: IoTDevice, alert_type: str, severity: str, 
                     title: str, message: str):
        """Create system alert"""
        # Check if similar alert already exists and is not resolved
        existing_alert = SystemAlert.objects.filter(
            device=device,
            alert_type=alert_type,
            is_resolved=False
        ).first()
        
        if not existing_alert:
            SystemAlert.objects.create(
                device=device,
                alert_type=alert_type,
                severity=severity,
                title=title,
                message=message,
                notification_sent=False
            )
    
    def _get_or_create_device(self, device_id: str) -> IoTDevice:
        """Get or create IoT device"""
        device, created = IoTDevice.objects.get_or_create(
            device_id=device_id,
            defaults={
                'name': f'Device {device_id}',
                'device_type': 'growth_chamber',
                'status': 'online'
            }
        )
        
        if created:
            # Create default configuration
            DeviceConfiguration.objects.create(device=device)
            logger.info(f"Created new device: {device_id}")
        
        return device
    
    def _get_sensor_unit(self, sensor_type: str) -> str:
        """Get unit for sensor type"""
        units = {
            'temperature': '°C',
            'humidity': '%',
            'soil_moisture': '%',
            'light': 'lux',
            'ph': 'pH',
            'ec': 'µS/cm',
            'co2': 'ppm',
            'pressure': 'hPa'
        }
        return units.get(sensor_type, '')
    
    def _mark_devices_offline(self):
        """Mark devices as offline if no heartbeat received"""
        timeout = timedelta(minutes=5)
        now = timezone.now()
        
        for device_id in list(self.active_devices):
            last_heartbeat = self.last_heartbeat.get(device_id)
            if last_heartbeat and (now - last_heartbeat) > timeout:
                try:
                    device = IoTDevice.objects.get(device_id=device_id)
                    device.is_online = False
                    device.status = 'offline'
                    device.save()
                    
                    # Create offline alert
                    self._create_alert(device, 'device_offline', 'error', 
                                     'Device Offline', f'Device {device_id} is offline')
                    
                    self.active_devices.discard(device_id)
                    logger.warning(f"Device {device_id} marked as offline")
                    
                except IoTDevice.DoesNotExist:
                    self.active_devices.discard(device_id)
    
    def _publish_service_status(self, status: str):
        """Publish service status to MQTT"""
        payload = {
            'service': 'agrosense_backend',
            'status': status,
            'timestamp': timezone.now().isoformat(),
            'version': '1.0.0'
        }
        
        self.publish_message('service/status', payload)
    
    def connect(self):
        """Connect to MQTT broker"""
        if self.client is None:
            self.setup_client()
        
        try:
            logger.info(f"Connecting to MQTT broker: {self.broker_host}:{self.broker_port}")
            self.client.connect(self.broker_host, self.broker_port, 60)
            self.client.loop_start()
            
            # Wait for connection
            for _ in range(10):  # 5 seconds timeout
                if self.is_connected:
                    break
                time.sleep(0.5)
            
            return self.is_connected
            
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from MQTT broker"""
        if self.client:
            self._publish_service_status("offline")
            self.client.loop_stop()
            self.client.disconnect()
            self.is_connected = False
    
    def publish_message(self, topic: str, payload: Dict[str, Any], qos: int = 1):
        """Publish message to MQTT topic"""
        if not self.is_connected:
            logger.warning("Not connected to MQTT broker")
            return False
        
        try:
            full_topic = f"{self.base_topic}/{topic}"
            message = json.dumps(payload)
            
            result = self.client.publish(full_topic, message, qos)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.debug(f"Published to {full_topic}")
                return True
            else:
                logger.error(f"Failed to publish to {full_topic}: {result.rc}")
                return False
                
        except Exception as e:
            logger.error(f"Error publishing message: {e}")
            return False
    
    def publish_command(self, device_id: str, command_type: str, payload: Dict[str, Any]):
        """Publish command to specific device"""
        topic = f"{device_id}/command/{command_type}"
        return self.publish_message(topic, payload)
    
    def publish_environment_settings(self, device_id: str, crop_environment: CropEnvironment):
        """Publish crop environment settings to device"""
        payload = {
            'command': 'set_environment',
            'environment': {
                'temperature': crop_environment.optimal_temperature,
                'humidity': crop_environment.optimal_humidity,
                'soil_moisture': crop_environment.optimal_soil_moisture,
                'light_hours': crop_environment.light_hours,
                'light_intensity': crop_environment.light_intensity,
                'tolerances': {
                    'temperature': crop_environment.temperature_tolerance,
                    'humidity': crop_environment.humidity_tolerance,
                    'moisture': crop_environment.moisture_tolerance
                }
            },
            'timestamp': timezone.now().isoformat()
        }
        
        return self.publish_command(device_id, 'environment', payload)
    
    def publish_manual_control(self, device_id: str, actuator_type: str, action: str, power_level: int = 100):
        """Publish manual control command"""
        payload = {
            'command': 'manual_control',
            'actuator': actuator_type,
            'action': action,
            'power_level': power_level,
            'timestamp': timezone.now().isoformat()
        }
        
        return self.publish_command(device_id, 'manual_control', payload)
    
    def publish_emergency_stop(self, device_id: str):
        """Publish emergency stop command"""
        payload = {
            'command': 'emergency_stop',
            'timestamp': timezone.now().isoformat()
        }
        
        return self.publish_command(device_id, 'emergency', payload)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get service statistics"""
        uptime = time.time() - self.stats['uptime_start']
        
        return {
            'uptime_seconds': uptime,
            'uptime_formatted': str(timedelta(seconds=int(uptime))),
            'messages_received': self.stats['messages_received'],
            'messages_sent': self.stats['messages_sent'],
            'connection_attempts': self.stats['connection_attempts'],
            'last_connection': self.stats['last_connection'],
            'active_devices': len(self.active_devices),
            'is_connected': self.is_connected
        }
    
    def run_forever(self):
        """Run MQTT service in blocking mode"""
        if not self.connect():
            logger.error("Failed to connect to MQTT broker")
            return
        
        try:
            logger.info("MQTT service started successfully")
            
            # Main loop
            while True:
                time.sleep(10)  # Check every 10 seconds
                
                # Check device heartbeats
                self._mark_devices_offline()
                
                # Reconnect if needed
                if not self.is_connected:
                    logger.info("Attempting to reconnect...")
                    self.connect()
                    
        except KeyboardInterrupt:
            logger.info("MQTT service stopped by user")
        except Exception as e:
            logger.error(f"MQTT service error: {e}")
        finally:
            self.disconnect()


# Global MQTT service instance
mqtt_service = MQTTService()


class Command(BaseCommand):
    """
    Django management command to run MQTT service
    Usage: python manage.py mqtt_service
    """
    help = 'Run MQTT service for Smart IoT Chamber communication'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--broker-host',
            type=str,
            default='broker.hivemq.com',
            help='MQTT broker hostname'
        )
        parser.add_argument(
            '--broker-port',
            type=int,
            default=8883,
            help='MQTT broker port'
        )
        parser.add_argument(
            '--use-tls',
            action='store_true',
            default=True,
            help='Use TLS encryption'
        )
    
    def handle(self, *args, **options):
        # Override settings with command line arguments
        if options['broker_host']:
            mqtt_service.broker_host = options['broker_host']
        if options['broker_port']:
            mqtt_service.broker_port = options['broker_port']
        if options['use_tls'] is not None:
            mqtt_service.use_tls = options['use_tls']
        
        self.stdout.write("Starting MQTT service for Smart IoT Chamber...")
        self.stdout.write(f"Broker: {mqtt_service.broker_host}:{mqtt_service.broker_port}")
        self.stdout.write(f"TLS: {mqtt_service.use_tls}")
        
        try:
            mqtt_service.run_forever()
        except KeyboardInterrupt:
            self.stdout.write("\nMQTT service stopped by user")
        except Exception as e:
            self.stderr.write(f"MQTT service error: {e}")
        
        self.stdout.write("MQTT service shutdown complete")
