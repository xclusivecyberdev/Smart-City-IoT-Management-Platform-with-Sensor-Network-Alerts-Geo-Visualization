#!/bin/bash
# Script to run multiple device simulators

BROKER=${MQTT_BROKER:-localhost}
PORT=${MQTT_PORT:-1883}
USERNAME=${MQTT_USERNAME:-iot_platform}
PASSWORD=${MQTT_PASSWORD:-mqtt_secure_pass}

echo "Starting Smart City IoT Device Simulators..."
echo "MQTT Broker: $BROKER:$PORT"

# Traffic Sensors
python3 traffic_sensor_simulator.py \
    --device-id traffic-sensor-001 \
    --broker $BROKER \
    --port $PORT \
    --username $USERNAME \
    --password $PASSWORD \
    --interval 30 &

python3 traffic_sensor_simulator.py \
    --device-id traffic-sensor-002 \
    --broker $BROKER \
    --port $PORT \
    --username $USERNAME \
    --password $PASSWORD \
    --interval 30 &

# Pollution Monitors
python3 pollution_monitor_simulator.py \
    --device-id pollution-monitor-001 \
    --broker $BROKER \
    --port $PORT \
    --username $USERNAME \
    --password $PASSWORD \
    --interval 60 &

python3 pollution_monitor_simulator.py \
    --device-id pollution-monitor-002 \
    --broker $BROKER \
    --port $PORT \
    --username $USERNAME \
    --password $PASSWORD \
    --interval 60 &

echo "Simulators started in background"
echo "Press Ctrl+C to stop all simulators"

# Wait for user interrupt
wait
