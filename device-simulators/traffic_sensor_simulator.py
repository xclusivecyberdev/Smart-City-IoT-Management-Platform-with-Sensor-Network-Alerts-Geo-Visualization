#!/usr/bin/env python3
"""
Traffic Sensor Simulator
Simulates a traffic monitoring sensor that sends vehicle count and speed data
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


class TrafficSensorSimulator:
    def __init__(self, device_id, mqtt_broker, mqtt_port, username, password, topic_prefix):
        self.device_id = device_id
        self.mqtt_broker = mqtt_broker
        self.mqtt_port = mqtt_port
        self.username = username
        self.password = password
        self.topic_prefix = topic_prefix
        self.client = None

        # Simulation state
        self.hour_of_day = datetime.now().hour

    def connect(self):
        """Connect to MQTT broker"""
        self.client = mqtt.Client(client_id=f"traffic_sensor_{self.device_id}")
        self.client.username_pw_set(self.username, self.password)
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect

        self.client.connect(self.mqtt_broker, self.mqtt_port, keepalive=60)
        self.client.loop_start()

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.info(f"Traffic sensor {self.device_id} connected to MQTT broker")
        else:
            logger.error(f"Failed to connect with code: {rc}")

    def _on_disconnect(self, client, userdata, rc):
        if rc != 0:
            logger.warning(f"Unexpected disconnection")

    def generate_data(self):
        """Generate simulated traffic data"""
        self.hour_of_day = datetime.now().hour

        # Simulate rush hour traffic patterns
        if 7 <= self.hour_of_day <= 9 or 17 <= self.hour_of_day <= 19:
            # Rush hour
            vehicle_count = random.randint(50, 100)
            average_speed = random.uniform(15, 35)  # km/h (slower during rush hour)
            congestion_level = random.choice(["high", "moderate"])
        elif 22 <= self.hour_of_day or self.hour_of_day <= 5:
            # Night time
            vehicle_count = random.randint(5, 15)
            average_speed = random.uniform(50, 70)
            congestion_level = "low"
        else:
            # Normal hours
            vehicle_count = random.randint(20, 50)
            average_speed = random.uniform(40, 60)
            congestion_level = random.choice(["low", "moderate"])

        return {
            "vehicle_count": vehicle_count,
            "average_speed": round(average_speed, 2),
            "congestion_level": congestion_level,
            "lane_occupancy": round(random.uniform(0.2, 0.9), 2),
            "incidents": random.randint(0, 2)
        }

    def send_data(self):
        """Send sensor data to MQTT broker"""
        data = self.generate_data()

        payload = {
            "device_id": self.device_id,
            "device_type": "traffic_sensor",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "data": data
        }

        topic = f"{self.topic_prefix}/devices/{self.device_id}/data"
        self.client.publish(topic, json.dumps(payload), qos=1)

        logger.info(f"[{self.device_id}] Sent: {data}")

    def send_status(self):
        """Send device status"""
        status_payload = {
            "device_id": self.device_id,
            "battery_level": round(random.uniform(70, 100), 1),
            "signal_strength": random.randint(-70, -30),
            "firmware_version": "1.2.3",
            "uptime_seconds": random.randint(10000, 1000000)
        }

        topic = f"{self.topic_prefix}/devices/{self.device_id}/status"
        self.client.publish(topic, json.dumps(status_payload), qos=1)

        logger.debug(f"[{self.device_id}] Sent status")

    def run(self, interval=30):
        """Run the simulator"""
        logger.info(f"Starting traffic sensor simulator: {self.device_id}")
        status_counter = 0

        try:
            while True:
                self.send_data()

                # Send status every 10 data transmissions
                status_counter += 1
                if status_counter >= 10:
                    self.send_status()
                    status_counter = 0

                time.sleep(interval)

        except KeyboardInterrupt:
            logger.info("Stopping simulator...")
            self.client.loop_stop()
            self.client.disconnect()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Traffic Sensor Simulator")
    parser.add_argument("--device-id", required=True, help="Device ID")
    parser.add_argument("--broker", default="localhost", help="MQTT broker host")
    parser.add_argument("--port", type=int, default=1883, help="MQTT broker port")
    parser.add_argument("--username", default="iot_platform", help="MQTT username")
    parser.add_argument("--password", default="mqtt_secure_pass", help="MQTT password")
    parser.add_argument("--topic-prefix", default="smartcity", help="MQTT topic prefix")
    parser.add_argument("--interval", type=int, default=30, help="Data send interval in seconds")

    args = parser.parse_args()

    simulator = TrafficSensorSimulator(
        device_id=args.device_id,
        mqtt_broker=args.broker,
        mqtt_port=args.port,
        username=args.username,
        password=args.password,
        topic_prefix=args.topic_prefix
    )

    simulator.connect()
    time.sleep(1)  # Wait for connection
    simulator.run(interval=args.interval)
