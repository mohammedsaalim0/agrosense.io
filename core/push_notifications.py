"""
Mobile Push Notifications for Smart IoT Chamber
Production-ready push notification system using OneSignal
Supports web push notifications and mobile app integration
"""

import json
import requests
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from .models import SystemAlert, IoTDevice
import logging

logger = logging.getLogger(__name__)


class PushNotificationService:
    """
    Production-ready push notification service
    Supports multiple providers (OneSignal, Firebase, Expo)
    """
    
    def __init__(self):
        self.provider = getattr(settings, 'PUSH_NOTIFICATION_PROVIDER', 'onesignal')
        self.api_key = getattr(settings, 'PUSH_NOTIFICATION_API_KEY', '')
        self.app_id = getattr(settings, 'PUSH_NOTIFICATION_APP_ID', '')
        
        if self.provider == 'onesignal':
            self.api_url = 'https://onesignal.com/api/v1/notifications'
            self.headers = {
                'Content-Type': 'application/json; charset=utf-8',
                'Authorization': f'Basic {self.api_key}'
            }
        elif self.provider == 'firebase':
            self.api_url = f'https://fcm.googleapis.com/fcm/send'
            self.headers = {
                'Content-Type': 'application/json',
                'Authorization': f'key={self.api_key}'
            }
        else:
            raise ImproperlyConfigured(f"Unsupported push notification provider: {self.provider}")
    
    def send_notification(self, title, message, data=None, segments=None, device_ids=None):
        """
        Send push notification
        """
        try:
            if self.provider == 'onesignal':
                return self._send_onesignal_notification(title, message, data, segments, device_ids)
            elif self.provider == 'firebase':
                return self._send_firebase_notification(title, message, data, device_ids)
        except Exception as e:
            logger.error(f"Error sending push notification: {e}")
            return False
    
    def _send_onesignal_notification(self, title, message, data=None, segments=None, device_ids=None):
        """
        Send notification using OneSignal
        """
        payload = {
            'app_id': self.app_id,
            'headings': {'en': title},
            'contents': {'en': message},
            'data': data or {},
        }
        
        if segments:
            payload['included_segments'] = segments
        elif device_ids:
            payload['include_player_ids'] = device_ids
        else:
            payload['included_segments'] = ['All']
        
        response = requests.post(self.api_url, headers=self.headers, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"OneSignal notification sent: {result.get('id')}")
            return True
        else:
            logger.error(f"OneSignal API error: {response.status_code} - {response.text}")
            return False
    
    def _send_firebase_notification(self, title, message, data=None, device_ids=None):
        """
        Send notification using Firebase Cloud Messaging
        """
        if not device_ids:
            logger.warning("Firebase requires specific device IDs")
            return False
        
        payload = {
            'notification': {
                'title': title,
                'body': message,
                'sound': 'default'
            },
            'data': data or {},
            'registration_ids': device_ids
        }
        
        response = requests.post(self.api_url, headers=self.headers, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Firebase notification sent: {result.get('success')} deliveries")
            return True
        else:
            logger.error(f"Firebase API error: {response.status_code} - {response.text}")
            return False
    
    def send_alert_notification(self, alert):
        """
        Send notification for system alert
        """
        # Determine notification priority based on alert severity
        priority_map = {
            'info': 'normal',
            'warning': 'high',
            'error': 'high',
            'critical': 'emergency'
        }
        
        priority = priority_map.get(alert.severity, 'normal')
        
        # Create notification data
        notification_data = {
            'type': 'alert',
            'alert_id': alert.id,
            'device_id': alert.device.device_id if alert.device else None,
            'severity': alert.severity,
            'timestamp': alert.created_at.isoformat()
        }
        
        # Add device-specific segment if alert is device-specific
        segments = ['All']
        if alert.device:
            segments = [f'Device_{alert.device.device_id}']
        
        # Send notification
        return self.send_notification(
            title=f"🚨 {alert.title}",
            message=alert.message,
            data=notification_data,
            segments=segments
        )
    
    def send_device_offline_notification(self, device):
        """
        Send notification when device goes offline
        """
        notification_data = {
            'type': 'device_offline',
            'device_id': device.device_id,
            'timestamp': timezone.now().isoformat()
        }
        
        return self.send_notification(
            title=f"📱 Device Offline: {device.name}",
            message=f"Device {device.name} ({device.device_id}) has gone offline",
            data=notification_data,
            segments=[f'Device_{device.device_id}']
        )
    
    def send_irrigation_notification(self, device, action, duration=None):
        """
        Send notification for irrigation events
        """
        if action == 'started':
            title = f"💧 Irrigation Started"
            message = f"Irrigation started for {device.name}"
            if duration:
                message += f" ({duration} seconds)"
        elif action == 'completed':
            title = f"💧 Irrigation Completed"
            message = f"Irrigation completed for {device.name}"
        else:
            return False
        
        notification_data = {
            'type': 'irrigation',
            'device_id': device.device_id,
            'action': action,
            'duration': duration,
            'timestamp': timezone.now().isoformat()
        }
        
        return self.send_notification(
            title=title,
            message=message,
            data=notification_data,
            segments=[f'Device_{device.device_id}']
        )
    
    def send_environment_notification(self, device, sensor_type, current_value, target_value):
        """
        Send notification for environmental condition alerts
        """
        sensor_emoji = {
            'temperature': '🌡️',
            'humidity': '💧',
            'soil_moisture': '🌱',
            'light': '💡'
        }
        
        emoji = sensor_emoji.get(sensor_type, '📊')
        
        notification_data = {
            'type': 'environment_alert',
            'device_id': device.device_id,
            'sensor_type': sensor_type,
            'current_value': current_value,
            'target_value': target_value,
            'timestamp': timezone.now().isoformat()
        }
        
        return self.send_notification(
            title=f"{emoji} Environmental Alert: {sensor_type.replace('_', ' ').title()}",
            message=f"{device.name}: {sensor_type.replace('_', ' ').title()} is {current_value} (target: {target_value})",
            data=notification_data,
            segments=[f'Device_{device.device_id}']
        )


# Global push notification service instance
push_service = PushNotificationService()


def send_alert_notification(alert):
    """
    Convenience function to send alert notification
    """
    return push_service.send_alert_notification(alert)


def send_device_offline_notification(device):
    """
    Convenience function to send device offline notification
    """
    return push_service.send_device_offline_notification(device)


def send_irrigation_notification(device, action, duration=None):
    """
    Convenience function to send irrigation notification
    """
    return push_service.send_irrigation_notification(device, action, duration)


def send_environment_notification(device, sensor_type, current_value, target_value):
    """
    Convenience function to send environment notification
    """
    return push_service.send_environment_notification(device, sensor_type, current_value, target_value)


# Django signal handlers for automatic notifications
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone


@receiver(post_save, sender=SystemAlert)
def alert_created_handler(sender, instance, created, **kwargs):
    """
    Automatically send push notification when alert is created
    """
    if created and not instance.notification_sent:
        # Send push notification
        success = send_alert_notification(instance)
        
        if success:
            # Mark notification as sent
            instance.notification_sent = True
            instance.notification_channels = ['push']
            instance.save(update_fields=['notification_sent', 'notification_channels'])


@receiver(post_save, sender=IoTDevice)
def device_status_changed_handler(sender, instance, **kwargs):
    """
    Send notification when device goes offline
    """
    if hasattr(instance, '_original_is_online'):
        if instance._original_is_online and not instance.is_online:
            # Device went offline
            send_device_offline_notification(instance)


# Pre-save signal to track device status changes
from django.db.models.signals import pre_save


@receiver(pre_save, sender=IoTDevice)
def device_status_tracker(sender, instance, **kwargs):
    """
    Track device status changes
    """
    if instance.pk:
        try:
            original = IoTDevice.objects.get(pk=instance.pk)
            instance._original_is_online = original.is_online
        except IoTDevice.DoesNotExist:
            pass
