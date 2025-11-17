# Smart City IoT Management Platform

> Enterprise-grade IoT platform for managing large-scale sensor networks deployed across smart cities

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![React](https://img.shields.io/badge/react-18.2+-blue.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)

## Overview

A comprehensive Smart City IoT Management Platform capable of managing thousands of IoT sensors deployed across a city, including traffic sensors, pollution monitors, parking meters, water-level sensors, garbage bin sensors, energy meters, weather stations, and public safety devices.

This platform provides:
- **Real-time data ingestion** via MQTT, WebSocket, and REST APIs
- **Device registry** with authentication, firmware tracking, and geolocation
- **Intelligent alerting** with threshold-based rules and real-time analytics
- **Geographic visualization** with interactive maps and heatmaps
- **Fleet management** for OTA updates and remote device control
- **Historical analytics** with time-series data and predictive ML models
- **Role-based access control** (RBAC) with audit logging

Similar to enterprise platforms like **Cisco Kinetic** or **Siemens MindSphere**.

## Features

### 🌐 Data Ingestion Pipeline
- **MQTT** broker integration for real-time sensor data
- **REST API** endpoints for HTTP-based data submission
- **WebSocket** support for bi-directional communication
- **Time-series database** (InfluxDB) for efficient storage
- **Batch ingestion** support for offline devices

### 📱 Device Registry & Management
- Device onboarding with certificate or API key authentication
- Firmware version tracking and OTA updates
- Geolocation tagging with zone management
- Real-time status monitoring (battery, signal strength, uptime)
- Configuration management and remote control
- Device metadata and custom tags

### 🚨 Intelligent Alerting System
- Configurable alert rules with multiple conditions
- Real-time threshold detection
- Anomaly detection using streaming analytics
- Multi-channel notifications (email, SMS, webhook)
- Alert suppression and aggregation
- Geofencing support

### 🗺️ Geographic Visualization
- Interactive map with device locations
- Status-based color coding
- Cluster overlays for dense deployments
- Heatmap visualization
- Time-series charts and analytics
- Zone-based filtering

### 🔧 Fleet Management
- Broadcast commands to device groups
- OTA firmware updates with scheduling
- Remote device restart and configuration
- Sampling rate adjustment
- Maintenance workflow management
- Bulk operations

### 📊 Analytics & Reporting
- Historical trend analysis
- Pollution patterns over time
- Traffic congestion analytics
- Energy consumption tracking
- Weather metrics and forecasting
- Predictive analytics with ML models

### 🔒 Security & Access Control
- JWT-based authentication
- Role-based access control (Admin, Engineer, Auditor)
- Device certificate validation
- API key management with rotation
- Audit logging for compliance
- TLS/SSL encryption support

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend Dashboard                       │
│         (React + Material-UI + Leaflet Maps)                │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTPS/WebSocket
┌────────────────────▼────────────────────────────────────────┐
│                   API Gateway (FastAPI)                      │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┐  │
│  │ Auth API │ Device   │ Alert    │ Fleet    │ Analytics│  │
│  │          │ Registry │ Rules    │ Mgmt     │          │  │
│  └──────────┴──────────┴──────────┴──────────┴──────────┘  │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
┌───────▼──────┐ ┌──▼────┐ ┌────▼──────────┐
│ PostgreSQL + │ │ Redis │ │   InfluxDB    │
│ TimescaleDB  │ │ Cache │ │ (Time-series) │
└──────────────┘ └───────┘ └───────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    MQTT Broker (Mosquitto)                   │
│                  IoT Device Communication                    │
└────────────────────┬────────────────────────────────────────┘
                     │
    ┌────────────────┼────────────────┐
    │                │                │
┌───▼────┐  ┌────────▼──────┐  ┌────▼──────┐
│Traffic │  │   Pollution   │  │  Energy   │
│Sensors │  │   Monitors    │  │  Meters   │
└────────┘  └───────────────┘  └───────────┘
```

## Tech Stack

### Backend
- **FastAPI** - Modern async Python web framework
- **PostgreSQL + TimescaleDB** - Relational and time-series data
- **InfluxDB** - High-performance time-series database
- **Redis** - Caching and pub/sub
- **SQLAlchemy** - ORM with async support
- **Paho MQTT** - MQTT client library
- **Celery** - Distributed task queue

### Frontend
- **React 18** - UI framework
- **Material-UI** - Component library
- **Leaflet** - Interactive maps
- **Recharts** - Data visualization
- **Socket.io** - Real-time communication

### Infrastructure
- **Docker & Docker Compose** - Containerization
- **Nginx** - Reverse proxy & load balancing
- **Mosquitto** - MQTT broker
- **Grafana** - Monitoring dashboards
- **Prometheus** - Metrics collection

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- Node.js 18+

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd Smart-City-IoT-Management-Platform-with-Sensor-Network-Alerts-Geo-Visualization
```

2. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Create MQTT password file**
```bash
# Create mosquitto password file
docker run -it --rm -v $(pwd)/config/mosquitto:/mosquitto/config eclipse-mosquitto:2 mosquitto_passwd -c /mosquitto/config/passwd iot_platform
# Enter password: mqtt_secure_pass
```

4. **Start all services**
```bash
docker-compose up -d
```

5. **Initialize the database**
```bash
docker-compose exec backend python -c "
from backend.core.database import init_db
import asyncio
asyncio.run(init_db())
"
```

6. **Create initial admin user**
```bash
docker-compose exec backend python scripts/create_admin.py
```

The platform will be available at:
- **Frontend Dashboard**: http://localhost:3000
- **API Documentation**: http://localhost:8000/api/docs
- **Grafana**: http://localhost:3001 (admin/admin)
- **InfluxDB UI**: http://localhost:8086

### Running Device Simulators

```bash
cd device-simulators
pip install -r requirements.txt

# Run traffic sensor simulator
python traffic_sensor_simulator.py --device-id traffic-001 --broker localhost

# Run pollution monitor
python pollution_monitor_simulator.py --device-id pollution-001 --broker localhost

# Or run all simulators at once
chmod +x run_simulators.sh
./run_simulators.sh
```

## API Documentation

### Authentication

All API requests (except login/register) require a JWT token in the Authorization header:

```bash
Authorization: Bearer <access_token>
```

### Device Registration

```bash
POST /api/v1/devices
Content-Type: application/json
Authorization: Bearer <token>

{
  "id": "traffic-sensor-001",
  "name": "Main Street Traffic Sensor",
  "device_type": "traffic_sensor",
  "latitude": 40.7128,
  "longitude": -74.0060,
  "zone": "downtown",
  "firmware_version": "1.2.3"
}
```

### Data Ingestion (Device API)

```bash
POST /api/v1/devices/{device_id}/data
Content-Type: application/json
Authorization: Bearer <device_api_key>

{
  "device_id": "traffic-sensor-001",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {
    "vehicle_count": 42,
    "average_speed": 35.5,
    "congestion_level": "moderate"
  }
}
```

### Create Alert Rule

```bash
POST /api/v1/alert-rules
Content-Type: application/json
Authorization: Bearer <token>

{
  "name": "High Pollution Alert",
  "device_type": "pollution_monitor",
  "metric_name": "pm25",
  "condition": "gt",
  "threshold_value": 55.0,
  "severity": "warning",
  "alert_type": "high_pollution",
  "notification_channels": ["email"],
  "notification_recipients": ["admin@smartcity.com"]
}
```

For complete API documentation, visit http://localhost:8000/api/docs after starting the services.

## Configuration

### Environment Variables

Key environment variables (see `.env.example` for complete list):

```bash
# Database
DATABASE_URL=postgresql+asyncpg://smartcity:password@localhost:5432/smartcity_iot
INFLUXDB_URL=http://localhost:8086
INFLUXDB_TOKEN=your-influxdb-token

# MQTT
MQTT_BROKER_HOST=localhost
MQTT_BROKER_PORT=1883
MQTT_USERNAME=iot_platform
MQTT_PASSWORD=mqtt_secure_pass

# Security
SECRET_KEY=your-jwt-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Alerting
SMTP_HOST=smtp.gmail.com
SMTP_USERNAME=alerts@smartcity.com
SMTP_PASSWORD=your-email-password
```

## Development

### Backend Development

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development

```bash
cd frontend
npm install
npm start
```

### Running Tests

```bash
# Backend tests
cd backend
pytest tests/ -v --cov

# Frontend tests
cd frontend
npm test
```

## Deployment

### Production Deployment

1. **Update environment variables** for production
2. **Enable TLS/SSL** in Nginx configuration
3. **Set strong passwords** for all services
4. **Enable authentication** on MQTT broker
5. **Configure firewall** rules
6. **Set up backup** strategy for databases

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed deployment guide.

## Security Best Practices

- ✅ All passwords stored as hashes (bcrypt)
- ✅ JWT tokens with expiration
- ✅ Device authentication via API keys or certificates
- ✅ HTTPS/TLS encryption in production
- ✅ Rate limiting on API endpoints
- ✅ Input validation and sanitization
- ✅ SQL injection prevention (parameterized queries)
- ✅ CORS configuration
- ✅ Audit logging for all actions

## Monitoring & Observability

- **Grafana Dashboards** - Pre-configured dashboards for system metrics
- **Prometheus Metrics** - API and system metrics collection
- **Application Logs** - Structured JSON logging
- **Alert Notifications** - Multi-channel alerting system

## Project Structure

```
├── backend/                 # FastAPI backend
│   ├── api/                # API route handlers
│   ├── core/               # Core configuration
│   ├── models/             # Database models
│   ├── schemas/            # Pydantic schemas
│   ├── services/           # Business logic
│   └── main.py             # Application entry point
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # Reusable components
│   │   ├── pages/          # Page components
│   │   └── services/       # API services
├── device-simulators/      # IoT device simulators
├── config/                 # Configuration files
├── database/               # Database initialization
├── docs/                   # Documentation
├── docker-compose.yml      # Docker orchestration
└── README.md              # This file
```

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](docs/CONTRIBUTING.md) for details.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For issues, questions, or contributions:
- Create an issue in the repository
- Contact: support@smartcityiot.example

## Acknowledgments

- Inspired by Cisco Kinetic and Siemens MindSphere
- Built with open-source technologies
- Community contributions welcome

---

**Built with ❤️ for Smart Cities**
