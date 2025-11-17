# Smart City IoT Platform - Quick Start Guide

## 🎉 Platform Successfully Created!

Your enterprise-grade Smart City IoT Management Platform is ready for deployment.

## 🚀 Quick Start (5 minutes)

### 1. Prerequisites Check
Ensure you have installed:
- Docker & Docker Compose
- Git

### 2. Setup Environment

```bash
# Navigate to project
cd Smart-City-IoT-Management-Platform-with-Sensor-Network-Alerts-Geo-Visualization

# Copy environment file
cp .env.example .env

# Create MQTT password file
docker run -it --rm \
  -v $(pwd)/config/mosquitto:/mosquitto/config \
  eclipse-mosquitto:2 \
  mosquitto_passwd -c /mosquitto/config/passwd iot_platform
# Enter password: mqtt_secure_pass
```

### 3. Start All Services

```bash
# Using Make (recommended)
make up

# Or using Docker Compose directly
docker-compose up -d
```

Wait ~30 seconds for services to initialize.

### 4. Initialize Database

```bash
# Create admin user
make admin-default
# Or interactively:
make admin
```

### 5. Access the Platform

Open your browser to:

- **Dashboard**: http://localhost:3000
  - Username: `admin`
  - Password: `admin123` (or your chosen password)

- **API Documentation**: http://localhost:8000/api/docs
- **Grafana Monitoring**: http://localhost:3001 (admin/admin)
- **InfluxDB**: http://localhost:8086

### 6. Test with Simulators

```bash
cd device-simulators
pip install -r requirements.txt
./run_simulators.sh
```

The simulators will start generating data for:
- Traffic sensors
- Pollution monitors

Watch the data flow in the dashboard!

## 📚 What's Included

### Backend Services
✅ FastAPI REST API (async, high-performance)
✅ PostgreSQL + TimescaleDB (relational + time-series)
✅ InfluxDB (optimized time-series storage)
✅ Redis (caching & pub/sub)
✅ MQTT Broker (Mosquitto)
✅ Prometheus & Grafana (monitoring)

### Core Features
✅ Device registry with authentication
✅ Multi-protocol data ingestion (MQTT/REST/WebSocket)
✅ Real-time alerting engine
✅ Geographic visualization
✅ Fleet management & OTA updates
✅ Role-based access control
✅ Historical analytics
✅ Audit logging

### Device Types Supported
- Traffic sensors
- Pollution monitors
- Parking meters
- Water level sensors
- Garbage bin sensors
- Energy meters
- Weather stations
- Public safety devices

## 🔧 Common Commands

```bash
# View logs
make logs

# Restart services
make restart

# Stop services
make down

# Clean everything
make clean

# Create admin user
make admin

# Backup database
make backup-db

# Check service status
make status

# Run tests
make test
```

## 📖 Documentation

- **README.md** - Project overview and features
- **docs/ARCHITECTURE.md** - System architecture
- **docs/DEPLOYMENT.md** - Deployment guide (dev/prod)
- **docs/API.md** - Complete API reference

## 🔐 Security Notes

⚠️ **IMPORTANT**: Before deploying to production:

1. Change all default passwords in `.env`
2. Generate strong SECRET_KEY (64+ characters)
3. Enable TLS/SSL (see docs/DEPLOYMENT.md)
4. Update MQTT passwords
5. Configure firewall rules
6. Enable database encryption

## 🌐 API Examples

### Register a Device
```bash
curl -X POST http://localhost:8000/api/v1/devices \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "sensor-001",
    "name": "Downtown Traffic Sensor",
    "device_type": "traffic_sensor",
    "latitude": 40.7128,
    "longitude": -74.0060,
    "zone": "downtown"
  }'
```

### Submit Sensor Data
```bash
curl -X POST http://localhost:8000/api/v1/devices/sensor-001/data \
  -H "Authorization: Bearer DEVICE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "sensor-001",
    "timestamp": "2024-01-15T10:30:00Z",
    "data": {
      "vehicle_count": 42,
      "average_speed": 35.5
    }
  }'
```

### Create Alert Rule
```bash
curl -X POST http://localhost:8000/api/v1/alert-rules \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "High Pollution Alert",
    "device_type": "pollution_monitor",
    "metric_name": "pm25",
    "condition": "gt",
    "threshold_value": 55.0,
    "severity": "warning",
    "alert_type": "high_pollution"
  }'
```

## 🐛 Troubleshooting

### Services won't start
```bash
# Check Docker is running
docker ps

# View service logs
docker-compose logs -f

# Restart services
docker-compose restart
```

### Database connection error
```bash
# Wait for database to be ready
docker-compose logs postgres

# Manually check connection
docker-compose exec postgres psql -U smartcity -d smartcity_iot
```

### MQTT connection failed
```bash
# Test MQTT broker
mosquitto_sub -h localhost -p 1883 -t "test" -u iot_platform -P mqtt_secure_pass

# Check broker logs
docker-compose logs mosquitto
```

## 🎯 Next Steps

1. **Explore the Dashboard** - Login and explore the UI
2. **Read API Docs** - Visit http://localhost:8000/api/docs
3. **Deploy Devices** - Register your IoT devices
4. **Configure Alerts** - Set up alert rules
5. **Customize** - Modify code to fit your needs
6. **Deploy to Production** - Follow docs/DEPLOYMENT.md

## 💡 Tips

- Use `make help` to see all available commands
- Check Grafana for system metrics
- Monitor InfluxDB for time-series data
- Use the API docs for testing endpoints
- Review logs regularly for issues

## 🆘 Support

- **Documentation**: Check `docs/` directory
- **API Reference**: http://localhost:8000/api/docs
- **Issues**: Create a GitHub issue
- **Architecture**: See docs/ARCHITECTURE.md

## 🎊 You're All Set!

Your Smart City IoT Management Platform is ready to manage thousands of IoT devices across your city.

Happy monitoring! 🏙️📡
