#!/usr/bin/env python3
"""
Pollution Monitor Simulator
Simulates an air quality monitoring sensor
"""

import json
import random
import time
from datetime import datetime
import paho.mqtt.client as mqtt
import argparse
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PollutionMonitorSimulator:
    def __init__(self, device_id, mqtt_broker, mqtt_port, username, password, topic_prefix):
        self.device_id = device_id
        self.mqtt_broker = mqtt_broker
        self.mqtt_port = mqtt_port
        self.username = username
        self.password = password
        self.topic_prefix = topic_prefix
        self.client = None

        # Base pollution levels (can be modified for different scenarios)
        self.base_pm25 = random.uniform(10, 30)
        self.base_pm10 = random.uniform(20, 50)

    def connect(self):
        """Connect to MQTT broker"""
        self.client = mqtt.Client(client_id=f"pollution_monitor_{self.device_id}")
        self.client.username_pw_set(self.username, self.password)
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect

        self.client.connect(self.mqtt_broker, self.mqtt_port, keepalive=60)
        self.client.loop_start()

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.info(f"Pollution monitor {self.device_id} connected to MQTT broker")
        else:
            logger.error(f"Failed to connect with code: {rc}")

    def _on_disconnect(self, client, userdata, rc):
        if rc != 0:
            logger.warning(f"Unexpected disconnection")

    def generate_data(self):
        """Generate simulated pollution data"""
        hour = datetime.now().hour

        # Add variation based on time of day
        if 7 <= hour <= 9 or 17 <= hour <= 19:
            # Rush hour - higher pollution
            variation_factor = random.uniform(1.5, 2.0)
        else:
            variation_factor = random.uniform(0.8, 1.2)

        # PM2.5 and PM10 (particulate matter)
        pm25 = max(0, self.base_pm25 * variation_factor + random.uniform(-5, 5))
        pm10 = max(0, self.base_pm10 * variation_factor + random.uniform(-10, 10))

        # Other pollutants
        no2 = random.uniform(10, 80)  # Nitrogen dioxide (µg/m³)
        co2 = random.uniform(350, 500)  # Carbon dioxide (ppm)
        o3 = random.uniform(20, 100)  # Ozone (µg/m³)
        co = random.uniform(0.1, 2.0)  # Carbon monoxide (mg/m³)
        so2 = random.uniform(5, 30)  # Sulfur dioxide (µg/m³)

        # Calculate AQI (simplified)
        aqi = self._calculate_aqi(pm25)

        return {
            "pm25": round(pm25, 2),
            "pm10": round(pm10, 2),
            "no2": round(no2, 2),
            "co2": round(co2, 2),
            "o3": round(o3, 2),
            "co": round(co, 2),
            "so2": round(so2, 2),
            "aqi": int(aqi),
            "temperature": round(random.uniform(15, 30), 1),
            "humidity": round(random.uniform(40, 80), 1)
        }

    def _calculate_aqi(self, pm25):
        """Calculate Air Quality Index based on PM2.5"""
        if pm25 <= 12:
            return 50
        elif pm25 <= 35.4:
            return 100
        elif pm25 <= 55.4:
            return 150
        elif pm25 <= 150.4:
            return 200
        elif pm25 <= 250.4:
            return 300
        else:
            return 400

    def send_data(self):
        """Send sensor data to MQTT broker"""
        data = self.generate_data()

        payload = {
            "device_id": self.device_id,
            "device_type": "pollution_monitor",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "data": data
        }

        topic = f"{self.topic_prefix}/devices/{self.device_id}/data"
        self.client.publish(topic, json.dumps(payload), qos=1)

        logger.info(f"[{self.device_id}] PM2.5: {data['pm25']}, AQI: {data['aqi']}")

        # Trigger alert if pollution is high
        if data['pm25'] > 55:
            self.send_alert(data)

    def send_alert(self, data):
        """Send alert for high pollution"""
        alert_payload = {
            "device_id": self.device_id,
            "alert_type": "high_pollution",
            "severity": "warning" if data['pm25'] < 150 else "critical",
            "message": f"High PM2.5 level detected: {data['pm25']} µg/m³",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

        topic = f"{self.topic_prefix}/devices/{self.device_id}/alert"
        self.client.publish(topic, json.dumps(alert_payload), qos=1)

        logger.warning(f"[{self.device_id}] ALERT: High pollution - PM2.5: {data['pm25']}")

    def send_status(self):
        """Send device status"""
        status_payload = {
            "device_id": self.device_id,
            "battery_level": round(random.uniform(60, 100), 1),
            "signal_strength": random.randint(-80, -40),
            "firmware_version": "2.1.0",
            "uptime_seconds": random.randint(10000, 1000000)
        }

        topic = f"{self.topic_prefix}/devices/{self.device_id}/status"
        self.client.publish(topic, json.dumps(status_payload), qos=1)

    def run(self, interval=60):
        """Run the simulator"""
        logger.info(f"Starting pollution monitor simulator: {self.device_id}")
        status_counter = 0

        try:
            while True:
                self.send_data()

                status_counter += 1
                if status_counter >= 5:
                    self.send_status()
                    status_counter = 0

                time.sleep(interval)

        except KeyboardInterrupt:
            logger.info("Stopping simulator...")
            self.client.loop_stop()
            self.client.disconnect()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pollution Monitor Simulator")
    parser.add_argument("--device-id", required=True, help="Device ID")
    parser.add_argument("--broker", default="localhost", help="MQTT broker host")
    parser.add_argument("--port", type=int, default=1883, help="MQTT broker port")
    parser.add_argument("--username", default="iot_platform", help="MQTT username")
    parser.add_argument("--password", default="mqtt_secure_pass", help="MQTT password")
    parser.add_argument("--topic-prefix", default="smartcity", help="MQTT topic prefix")
    parser.add_argument("--interval", type=int, default=60, help="Data send interval in seconds")

    args = parser.parse_args()

    simulator = PollutionMonitorSimulator(
        device_id=args.device_id,
        mqtt_broker=args.broker,
        mqtt_port=args.port,
        username=args.username,
        password=args.password,
        topic_prefix=args.topic_prefix
    )

    simulator.connect()
    time.sleep(1)
    simulator.run(interval=args.interval)
