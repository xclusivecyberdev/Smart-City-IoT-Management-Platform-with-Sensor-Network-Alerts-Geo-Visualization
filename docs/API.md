# API Documentation - Smart City IoT Platform

## Base URL

```
Development: http://localhost:8000
Production:  https://api.yourdomain.com
```

## API Prefix

All endpoints are prefixed with `/api/v1`

## Authentication

The API uses JWT (JSON Web Token) authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your_access_token>
```

### Getting an Access Token

**Endpoint:** `POST /api/v1/auth/login`

**Request:**
```json
{
  "username": "admin",
  "password": "your_password"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Token Expiration:**
- Access Token: 30 minutes
- Refresh Token: 7 days

## API Endpoints

### Authentication

#### Register User
```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "SecurePass123",
  "full_name": "John Doe",
  "role": "viewer"
}
```

#### Login
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}
```

#### Get Current User
```http
GET /api/v1/auth/me
Authorization: Bearer <token>
```

### Devices

#### Create Device
```http
POST /api/v1/devices
Authorization: Bearer <token>
Content-Type: application/json

{
  "id": "traffic-sensor-001",
  "name": "Main Street Traffic Sensor",
  "device_type": "traffic_sensor",
  "latitude": 40.7128,
  "longitude": -74.0060,
  "zone": "downtown",
  "firmware_version": "1.2.3",
  "manufacturer": "SmartSensors Inc",
  "model": "TS-2000",
  "sampling_rate_seconds": 60
}
```

**Response:**
```json
{
  "id": "traffic-sensor-001",
  "name": "Main Street Traffic Sensor",
  "device_type": "traffic_sensor",
  "status": "active",
  "latitude": 40.7128,
  "longitude": -74.0060,
  "zone": "downtown",
  "firmware_version": "1.2.3",
  "created_at": "2024-01-15T10:30:00Z",
  "metadata": {
    "api_key": "abc123..."  // Only returned on creation
  }
}
```

#### List Devices
```http
GET /api/v1/devices?page=1&page_size=50&device_type=traffic_sensor&status=active
Authorization: Bearer <token>
```

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `page_size` (int): Items per page (default: 50, max: 100)
- `device_type` (string): Filter by device type
- `status` (string): Filter by status (active, offline, maintenance)
- `zone` (string): Filter by zone
- `search` (string): Search by name or ID

**Response:**
```json
{
  "devices": [...],
  "total": 150,
  "page": 1,
  "page_size": 50
}
```

#### Get Device
```http
GET /api/v1/devices/{device_id}
Authorization: Bearer <token>
```

#### Update Device
```http
PUT /api/v1/devices/{device_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "status": "maintenance",
  "firmware_version": "1.3.0"
}
```

#### Delete Device
```http
DELETE /api/v1/devices/{device_id}
Authorization: Bearer <token>
```

### Data Ingestion (Device Endpoints)

#### Submit Sensor Data
```http
POST /api/v1/devices/{device_id}/data
Authorization: Bearer <device_api_key>
Content-Type: application/json

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

#### Submit Batch Data
```http
POST /api/v1/devices/{device_id}/data/batch
Authorization: Bearer <device_api_key>
Content-Type: application/json

{
  "device_id": "traffic-sensor-001",
  "data_points": [
    {
      "timestamp": "2024-01-15T10:30:00Z",
      "vehicle_count": 42,
      "average_speed": 35.5
    },
    {
      "timestamp": "2024-01-15T10:31:00Z",
      "vehicle_count": 45,
      "average_speed": 33.2
    }
  ]
}
```

#### Get Device Data
```http
GET /api/v1/devices/{device_id}/data?start_time=-1h&stop_time=now()
Authorization: Bearer <token>
```

**Query Parameters:**
- `start_time` (string): Start time (e.g., "-1h", "-24h", "2024-01-15T00:00:00Z")
- `stop_time` (string): Stop time (e.g., "now()", "2024-01-15T23:59:59Z")

### Alert Rules

#### Create Alert Rule
```http
POST /api/v1/alert-rules
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "High PM2.5 Alert",
  "description": "Alert when PM2.5 exceeds safe levels",
  "device_type": "pollution_monitor",
  "metric_name": "pm25",
  "condition": "gt",
  "threshold_value": 55.0,
  "severity": "warning",
  "alert_type": "high_pollution",
  "notification_channels": ["email"],
  "notification_recipients": ["admin@city.gov"],
  "is_enabled": true
}
```

**Condition Types:**
- `gt`: Greater than
- `gte`: Greater than or equal
- `lt`: Less than
- `lte`: Less than or equal
- `eq`: Equal to
- `between`: Between min and max

**Severity Levels:**
- `info`
- `warning`
- `critical`
- `emergency`

#### List Alert Rules
```http
GET /api/v1/alert-rules
Authorization: Bearer <token>
```

#### Get Alert Rule
```http
GET /api/v1/alert-rules/{rule_id}
Authorization: Bearer <token>
```

#### Update Alert Rule
```http
PUT /api/v1/alert-rules/{rule_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "threshold_value": 65.0,
  "is_enabled": false
}
```

#### Delete Alert Rule
```http
DELETE /api/v1/alert-rules/{rule_id}
Authorization: Bearer <token>
```

### Alerts

#### List Alerts
```http
GET /api/v1/alerts?page=1&status=open&severity=critical
Authorization: Bearer <token>
```

**Query Parameters:**
- `status` (string): Filter by status (open, acknowledged, resolved, closed)
- `severity` (string): Filter by severity
- `alert_type` (string): Filter by alert type
- `device_id` (string): Filter by device

#### Get Alert
```http
GET /api/v1/alerts/{alert_id}
Authorization: Bearer <token>
```

#### Acknowledge Alert
```http
POST /api/v1/alerts/{alert_id}/acknowledge
Authorization: Bearer <token>
Content-Type: application/json

{
  "notes": "Investigating the issue"
}
```

#### Resolve Alert
```http
POST /api/v1/alerts/{alert_id}/resolve
Authorization: Bearer <token>
Content-Type: application/json

{
  "resolution_notes": "Sensor recalibrated, issue resolved"
}
```

### Fleet Management

#### Send Command to Devices
```http
POST /api/v1/fleet/commands
Authorization: Bearer <token>
Content-Type: application/json

{
  "command": "restart",
  "device_ids": ["device-001", "device-002"],
  "parameters": {}
}
```

**Common Commands:**
- `restart`: Restart device
- `update_config`: Push new configuration
- `update_sampling_rate`: Change sampling rate
- `ota_update`: Trigger firmware update

#### Broadcast Command
```http
POST /api/v1/fleet/broadcast/{device_type}
Authorization: Bearer <token>
Content-Type: application/json

{
  "command": "update_sampling_rate",
  "parameters": {
    "sampling_rate_seconds": 120
  }
}
```

#### Schedule Firmware Update
```http
POST /api/v1/fleet/firmware-updates
Authorization: Bearer <token>
Content-Type: application/json

{
  "device_ids": ["device-001", "device-002"],
  "to_version": "2.0.0",
  "firmware_url": "https://storage.example.com/firmware/v2.0.0.bin",
  "checksum": "sha256:abc123...",
  "scheduled_at": "2024-01-16T02:00:00Z"
}
```

#### List Firmware Updates
```http
GET /api/v1/fleet/firmware-updates?device_id=device-001
Authorization: Bearer <token>
```

#### Create Maintenance Log
```http
POST /api/v1/fleet/maintenance
Authorization: Bearer <token>
Content-Type: application/json

{
  "device_id": "device-001",
  "maintenance_type": "calibration",
  "description": "Annual sensor calibration",
  "scheduled_at": "2024-01-20T09:00:00Z"
}
```

### Analytics

#### Dashboard Summary
```http
GET /api/v1/analytics/dashboard/summary
Authorization: Bearer <token>
```

**Response:**
```json
{
  "devices": {
    "total": 500,
    "active": 485,
    "offline": 15,
    "by_type": {
      "traffic_sensor": 100,
      "pollution_monitor": 50,
      "parking_meter": 200,
      "energy_meter": 150
    }
  },
  "alerts": {
    "active": 23,
    "critical": 5
  }
}
```

#### Device Map Data
```http
GET /api/v1/analytics/devices/map?device_type=traffic_sensor
Authorization: Bearer <token>
```

**Response (GeoJSON):**
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [-74.0060, 40.7128]
      },
      "properties": {
        "id": "traffic-001",
        "name": "Main St Sensor",
        "device_type": "traffic_sensor",
        "status": "active"
      }
    }
  ]
}
```

#### Time-Series Data
```http
GET /api/v1/analytics/time-series/pollution_monitor/pm25?aggregation=mean&window=1h&start_time=-24h
Authorization: Bearer <token>
```

**Query Parameters:**
- `aggregation` (string): Aggregation function (mean, sum, min, max, count)
- `window` (string): Time window (1m, 5m, 1h, 1d)
- `start_time` (string): Start time

#### Pollution Trends
```http
GET /api/v1/analytics/pollution/trends?start_time=-30d&window=1d
Authorization: Bearer <token>
```

#### Traffic Congestion
```http
GET /api/v1/analytics/traffic/congestion?zone=downtown&start_time=-24h
Authorization: Bearer <token>
```

#### Energy Consumption
```http
GET /api/v1/analytics/energy/consumption?zone=district1&start_time=-7d&window=1h
Authorization: Bearer <token>
```

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error message here"
}
```

**HTTP Status Codes:**
- `200` - Success
- `201` - Created
- `204` - No Content (successful deletion)
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `422` - Validation Error
- `500` - Internal Server Error

**Validation Error Example:**
```json
{
  "detail": [
    {
      "loc": ["body", "latitude"],
      "msg": "ensure this value is greater than or equal to -90",
      "type": "value_error.number.not_ge"
    }
  ]
}
```

## Rate Limiting

- User endpoints: 60 requests/minute
- Device endpoints: 1000 requests/minute

Headers include:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1610000000
```

## Pagination

List endpoints support pagination:

**Request:**
```http
GET /api/v1/devices?page=2&page_size=50
```

**Response includes:**
```json
{
  "items": [...],
  "total": 500,
  "page": 2,
  "page_size": 50
}
```

## WebSocket API

### Real-time Data Stream

**Connect:**
```javascript
const ws = new WebSocket('ws://localhost:8001/ws');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};
```

**Message Types:**
- `device_data`: Sensor data update
- `alert`: New alert triggered
- `device_status`: Device status change

## SDK Examples

### Python

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

# Login
response = requests.post(f"{BASE_URL}/auth/login", json={
    "username": "admin",
    "password": "admin123"
})
token = response.json()["access_token"]

# Get devices
headers = {"Authorization": f"Bearer {token}"}
devices = requests.get(f"{BASE_URL}/devices", headers=headers).json()

# Submit sensor data (device)
device_headers = {"Authorization": f"Bearer {device_api_key}"}
requests.post(
    f"{BASE_URL}/devices/sensor-001/data",
    headers=device_headers,
    json={
        "device_id": "sensor-001",
        "timestamp": "2024-01-15T10:30:00Z",
        "data": {"temperature": 22.5}
    }
)
```

### JavaScript

```javascript
const BASE_URL = 'http://localhost:8000/api/v1';

// Login
const login = async () => {
  const response = await fetch(`${BASE_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      username: 'admin',
      password: 'admin123'
    })
  });
  const { access_token } = await response.json();
  return access_token;
};

// Get devices
const getDevices = async (token) => {
  const response = await fetch(`${BASE_URL}/devices`, {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  return await response.json();
};
```

---

For interactive API documentation, visit: **http://localhost:8000/api/docs**
