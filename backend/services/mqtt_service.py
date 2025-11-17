import asyncio
import json
import logging
from typing import Callable, Optional
from datetime import datetime
import paho.mqtt.client as mqtt
from ..core.config import settings
from .influxdb import influxdb_service
from .alert_service import alert_service

logger = logging.getLogger(__name__)


class MQTTService:
    """MQTT Service for IoT data ingestion"""

    def __init__(self):
        self.client: Optional[mqtt.Client] = None
        self.connected = False
        self.message_callbacks = []

    def connect(self):
        """Connect to MQTT broker"""
        try:
            self.client = mqtt.Client(client_id="smartcity_platform")
            self.client.username_pw_set(settings.MQTT_USERNAME, settings.MQTT_PASSWORD)

            # Set callbacks
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message = self._on_message

            # Connect to broker
            self.client.connect(
                settings.MQTT_BROKER_HOST,
                settings.MQTT_BROKER_PORT,
                keepalive=60
            )

            # Start network loop in background
            self.client.loop_start()
            logger.info(f"MQTT client connecting to {settings.MQTT_BROKER_HOST}:{settings.MQTT_BROKER_PORT}")

        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            raise

    def disconnect(self):
        """Disconnect from MQTT broker"""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            logger.info("Disconnected from MQTT broker")

    def _on_connect(self, client, userdata, flags, rc):
        """Callback when connected to MQTT broker"""
        if rc == 0:
            self.connected = True
            logger.info("Connected to MQTT broker")

            # Subscribe to all device topics
            topics = [
                (f"{settings.MQTT_TOPIC_PREFIX}/devices/+/data", settings.MQTT_QOS),
                (f"{settings.MQTT_TOPIC_PREFIX}/devices/+/status", settings.MQTT_QOS),
                (f"{settings.MQTT_TOPIC_PREFIX}/devices/+/alert", settings.MQTT_QOS),
            ]

            for topic, qos in topics:
                client.subscribe(topic, qos)
                logger.info(f"Subscribed to topic: {topic}")
        else:
            logger.error(f"Failed to connect to MQTT broker with code: {rc}")

    def _on_disconnect(self, client, userdata, rc):
        """Callback when disconnected from MQTT broker"""
        self.connected = False
        if rc != 0:
            logger.warning(f"Unexpected MQTT disconnection. Code: {rc}")
        else:
            logger.info("Disconnected from MQTT broker")

    def _on_message(self, client, userdata, msg):
        """Callback when message is received"""
        try:
            # Parse topic
            topic_parts = msg.topic.split('/')
            if len(topic_parts) < 4:
                logger.warning(f"Invalid topic format: {msg.topic}")
                return

            device_id = topic_parts[2]
            message_type = topic_parts[3]  # data, status, alert

            # Parse payload
            try:
                payload = json.loads(msg.payload.decode('utf-8'))
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON payload from {device_id}")
                return

            logger.debug(f"Received {message_type} from device {device_id}: {payload}")

            # Process based on message type
            if message_type == "data":
                self._process_sensor_data(device_id, payload)
            elif message_type == "status":
                self._process_device_status(device_id, payload)
            elif message_type == "alert":
                self._process_device_alert(device_id, payload)

            # Call registered callbacks
            for callback in self.message_callbacks:
                try:
                    callback(device_id, message_type, payload)
                except Exception as e:
                    logger.error(f"Error in message callback: {e}")

        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")

    def _process_sensor_data(self, device_id: str, payload: dict):
        """Process sensor data message"""
        try:
            # Extract data and metadata
            data = payload.get('data', {})
            device_type = payload.get('device_type', 'unknown')
            timestamp_str = payload.get('timestamp')

            # Parse timestamp
            if timestamp_str:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            else:
                timestamp = datetime.utcnow()

            # Write to InfluxDB
            influxdb_service.write_sensor_data(
                device_id=device_id,
                device_type=device_type,
                data=data,
                timestamp=timestamp
            )

            # Check alert rules (async call in background)
            asyncio.create_task(
                alert_service.evaluate_rules_for_device(device_id, device_type, data)
            )

            logger.debug(f"Processed sensor data from {device_id}")

        except Exception as e:
            logger.error(f"Error processing sensor data: {e}")

    def _process_device_status(self, device_id: str, payload: dict):
        """Process device status message"""
        try:
            # Update device status in database
            # This would typically update the device's last_seen, battery_level, signal_strength, etc.
            logger.info(f"Device {device_id} status: {payload}")

            # Could trigger alerts if device goes offline, battery low, etc.

        except Exception as e:
            logger.error(f"Error processing device status: {e}")

    def _process_device_alert(self, device_id: str, payload: dict):
        """Process device-generated alert"""
        try:
            logger.warning(f"Device {device_id} generated alert: {payload}")
            # Process device-side alerts

        except Exception as e:
            logger.error(f"Error processing device alert: {e}")

    def publish(self, topic: str, payload: dict, qos: int = None):
        """Publish message to MQTT topic"""
        if not self.connected:
            logger.error("Cannot publish: Not connected to MQTT broker")
            return False

        try:
            qos = qos if qos is not None else settings.MQTT_QOS
            result = self.client.publish(
                topic,
                json.dumps(payload),
                qos=qos
            )

            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.debug(f"Published to {topic}: {payload}")
                return True
            else:
                logger.error(f"Failed to publish to {topic}")
                return False

        except Exception as e:
            logger.error(f"Error publishing to MQTT: {e}")
            return False

    def send_command_to_device(self, device_id: str, command: str, parameters: dict = None):
        """Send command to device via MQTT"""
        topic = f"{settings.MQTT_TOPIC_PREFIX}/devices/{device_id}/commands"
        payload = {
            "command": command,
            "parameters": parameters or {},
            "timestamp": datetime.utcnow().isoformat()
        }
        return self.publish(topic, payload)

    def broadcast_command(self, device_type: str, command: str, parameters: dict = None):
        """Broadcast command to all devices of a type"""
        topic = f"{settings.MQTT_TOPIC_PREFIX}/broadcast/{device_type}/commands"
        payload = {
            "command": command,
            "parameters": parameters or {},
            "timestamp": datetime.utcnow().isoformat()
        }
        return self.publish(topic, payload)

    def register_message_callback(self, callback: Callable):
        """Register a callback for MQTT messages"""
        self.message_callbacks.append(callback)

    def unregister_message_callback(self, callback: Callable):
        """Unregister a callback"""
        if callback in self.message_callbacks:
            self.message_callbacks.remove(callback)


# Global instance
mqtt_service = MQTTService()
