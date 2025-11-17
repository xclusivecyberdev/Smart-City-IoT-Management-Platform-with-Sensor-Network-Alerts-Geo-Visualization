# Smart City IoT Platform - Architecture Documentation

## System Architecture Overview

The Smart City IoT Management Platform is built using a microservices-inspired architecture with the following key components:

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Client Applications                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │ Web Dashboard│  │ Mobile Apps  │  │ External Integrations    │  │
│  │  (React)     │  │              │  │  (Weather API, Traffic)  │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────────┘  │
└─────────┼──────────────────┼────────────────────┼──────────────────┘
          │                  │                    │
          └──────────────────┼────────────────────┘
                             │
                    ┌────────▼─────────┐
                    │  Nginx (Reverse  │
                    │  Proxy & LB)     │
                    └────────┬─────────┘
                             │
          ┌──────────────────┴──────────────────┐
          │                                     │
┌─────────▼──────────┐              ┌──────────▼──────────┐
│  FastAPI Backend   │◄─────────────│   WebSocket Server  │
│  (REST API)        │              │   (Real-time)       │
└────┬────┬────┬─────┘              └─────────────────────┘
     │    │    │
     │    │    └─────────────────┐
     │    │                      │
┌────▼────▼─────┐     ┌─────────▼──────┐     ┌──────────────┐
│  PostgreSQL + │     │    InfluxDB    │     │    Redis     │
│  TimescaleDB  │     │  (Time-series) │     │   (Cache)    │
└───────────────┘     └────────────────┘     └──────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    MQTT Broker (Mosquitto)                   │
│               Device-to-Platform Communication               │
└────────────────────┬────────────────────────────────────────┘
                     │
     ┌───────────────┼───────────────┐
     │               │               │
┌────▼─────┐  ┌─────▼─────┐  ┌─────▼──────┐
│  IoT     │  │    IoT    │  │    IoT     │
│ Devices  │  │  Devices  │  │  Devices   │
└──────────┘  └───────────┘  └────────────┘
```

## Core Components

### 1. API Gateway Layer (FastAPI)

**Purpose**: Central entry point for all client requests

**Responsibilities**:
- Request routing and validation
- Authentication and authorization
- Rate limiting
- Request/response transformation
- API documentation (OpenAPI/Swagger)

**Endpoints**:
- `/api/v1/auth/*` - Authentication
- `/api/v1/devices/*` - Device management
- `/api/v1/alerts/*` - Alert management
- `/api/v1/fleet/*` - Fleet operations
- `/api/v1/analytics/*` - Analytics and reporting

**Technology**: FastAPI with async/await for high concurrency

### 2. Data Layer

#### PostgreSQL + TimescaleDB
**Purpose**: Primary relational database with time-series capabilities

**Schema**:
- `users` - User accounts and authentication
- `devices` - Device registry and metadata
- `alerts` - Alert instances
- `alert_rules` - Alert rule definitions
- `firmware_updates` - OTA update tracking
- `maintenance_logs` - Maintenance records
- `audit_logs` - System audit trail

**Extensions**:
- TimescaleDB for time-series optimizations
- UUID for distributed ID generation
- Full-text search capabilities

#### InfluxDB
**Purpose**: High-performance time-series data storage

**Buckets**:
- `iot_sensors` - All sensor data points

**Data Model**:
```
Measurement: sensor_data
Tags: device_id, device_type, zone
Fields: metric values (pm25, temperature, vehicle_count, etc.)
Timestamp: RFC3339 nanosecond precision
```

**Retention Policies**:
- Raw data: 90 days
- 1-hour aggregations: 1 year
- Daily aggregations: 5 years

#### Redis
**Purpose**: High-speed caching and message broker

**Usage**:
- Session storage
- API response caching
- Real-time data pub/sub
- Rate limiting counters
- Celery task queue

### 3. Message Broker (MQTT)

**Purpose**: Bi-directional communication with IoT devices

**Topics Structure**:
```
smartcity/
├── devices/{device_id}/
│   ├── data           # Device publishes sensor data
│   ├── status         # Device health and status
│   ├── alerts         # Device-generated alerts
│   └── commands       # Platform sends commands
└── broadcast/{device_type}/
    └── commands       # Broadcast to all devices of type
```

**QoS Levels**:
- QoS 0: Fire and forget (status updates)
- QoS 1: At least once delivery (sensor data)
- QoS 2: Exactly once delivery (critical commands)

**Security**:
- Username/password authentication
- TLS/SSL encryption (production)
- ACL-based topic permissions

### 4. Alert Engine

**Components**:
- **Rule Evaluator**: Evaluates incoming data against rules
- **Event Detector**: ML-based anomaly detection
- **Notification Manager**: Multi-channel notifications
- **Suppression Engine**: Prevents alert fatigue

**Rule Types**:
1. **Threshold Rules**: Simple comparisons (>, <, ==, etc.)
2. **Time-Window Rules**: Aggregations over time
3. **Geofence Rules**: Location-based triggers
4. **Composite Rules**: Multiple conditions (AND/OR)

**Notification Channels**:
- Email (SMTP)
- SMS (Twilio/custom)
- Webhook (HTTP POST)
- Push notifications
- In-app notifications

### 5. Analytics Engine

**Real-time Analytics**:
- Stream processing of incoming data
- Moving averages and aggregations
- Trend detection
- Correlation analysis

**Historical Analytics**:
- Time-series queries (InfluxDB)
- Aggregations (hourly, daily, monthly)
- Custom reports generation
- Data export (CSV, JSON)

**Predictive Analytics**:
- ML models (scikit-learn, Prophet)
- Traffic prediction
- Pollution forecasting
- Anomaly detection
- Maintenance prediction

### 6. Fleet Management

**Capabilities**:
- **OTA Updates**: Over-the-air firmware deployment
- **Remote Commands**: Restart, reconfigure, diagnostics
- **Batch Operations**: Bulk device management
- **Scheduling**: Deferred operations
- **Rollback**: Update failure recovery

**Command Flow**:
```
API Request → Validation → Queue → MQTT Publish → Device
                                     ↓
                              Acknowledgment
                                     ↓
                              Status Update
```

## Data Flow Diagrams

### 1. Device Registration Flow

```
Device → REST API → Validation → Auth Service
                                      ↓
                              Generate API Key
                                      ↓
                              Create DB Record
                                      ↓
                              Return Credentials
```

### 2. Sensor Data Ingestion Flow

```
Device → MQTT Publish → MQTT Broker → Backend Subscriber
                                            ↓
                                    Parse & Validate
                                            ↓
                         ┌──────────────────┴──────────────────┐
                         │                                     │
                   Save to InfluxDB                    Evaluate Alert Rules
                         │                                     │
                   Acknowledge                         Trigger Alerts?
                                                              │
                                                      Send Notifications
```

### 3. Alert Processing Flow

```
Sensor Data → Rule Evaluator → Condition Met?
                                      ↓ Yes
                              Check Suppression
                                      ↓
                              Create Alert
                                      ↓
                         ┌────────────┴────────────┐
                         │                         │
                  Save to Database         Notification Manager
                                                   ↓
                                   ┌───────────────┼───────────────┐
                                   │               │               │
                               Email            SMS            Webhook
```

### 4. User Authentication Flow

```
Login Request → Validate Credentials → Check Password Hash
                                              ↓
                                        Generate JWT
                                              ↓
                                    ┌─────────┴─────────┐
                                    │                   │
                            Access Token        Refresh Token
                                    │                   │
                            (30 min TTL)        (7 day TTL)
```

## Security Architecture

### Authentication & Authorization

**User Authentication**:
- JWT (JSON Web Tokens)
- Access tokens (30 min)
- Refresh tokens (7 days)
- Password hashing (bcrypt)

**Device Authentication**:
- API Key authentication
- Certificate-based authentication (X.509)
- Device fingerprinting

**Authorization**:
- Role-based access control (RBAC)
- Roles: Admin, Engineer, Auditor, Operator, Viewer
- Permission-based fine-grained access

### Data Security

**Encryption**:
- TLS 1.3 for all communications (production)
- Data at rest encryption (database level)
- Encrypted environment variables

**Input Validation**:
- Pydantic models for schema validation
- SQL injection prevention (parameterized queries)
- XSS protection
- CSRF tokens

**Audit Logging**:
- All user actions logged
- Device operations tracked
- Immutable audit trail
- Compliance reporting

## Scalability Considerations

### Horizontal Scaling

**API Layer**:
- Stateless FastAPI instances
- Load balancing (Nginx/HAProxy)
- Auto-scaling based on CPU/memory

**Database Layer**:
- PostgreSQL read replicas
- TimescaleDB distributed hypertables
- InfluxDB clustering
- Redis Sentinel for HA

**MQTT Broker**:
- Mosquitto clustering
- Shared subscriptions
- Bridge mode for multi-region

### Performance Optimizations

**Caching Strategy**:
- Redis caching for frequently accessed data
- CDN for static assets
- Client-side caching (React Query)

**Database Optimizations**:
- Indexes on frequently queried fields
- Partitioning by time (TimescaleDB)
- Connection pooling
- Query optimization

**Async Processing**:
- Async/await in Python
- Background tasks (Celery)
- Message queues (Redis)

## Monitoring & Observability

### Metrics Collection

**Application Metrics** (Prometheus):
- Request rate, latency, error rate
- Database query performance
- MQTT message throughput
- Cache hit/miss ratio

**System Metrics**:
- CPU, memory, disk usage
- Network I/O
- Container health

**Business Metrics**:
- Active devices count
- Alert frequency
- Data ingestion rate
- API usage patterns

### Logging

**Structured Logging** (JSON):
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "service": "backend",
  "module": "device_service",
  "message": "Device registered",
  "device_id": "traffic-001",
  "user_id": "admin-123"
}
```

**Log Aggregation**:
- Centralized logging (ELK stack optional)
- Log rotation and retention
- Real-time log streaming

### Alerting

**System Alerts**:
- High error rate
- Database connection failures
- Disk space low
- Service unavailability

**Notification Channels**:
- PagerDuty integration
- Slack notifications
- Email alerts

## Disaster Recovery

### Backup Strategy

**Databases**:
- Automated daily backups
- Point-in-time recovery
- Cross-region replication (production)

**Configuration**:
- Version-controlled configs (Git)
- Secrets in vault (HashiCorp Vault)

### Recovery Procedures

**RTO** (Recovery Time Objective): 4 hours
**RPO** (Recovery Point Objective): 15 minutes

**Failover**:
- Database failover (automatic)
- Service redundancy
- Health checks and auto-restart

## Technology Choices Rationale

| Technology | Rationale |
|------------|-----------|
| **FastAPI** | High performance, async support, automatic OpenAPI docs |
| **PostgreSQL + TimescaleDB** | Reliable RDBMS + time-series optimization |
| **InfluxDB** | Purpose-built for time-series data, excellent query performance |
| **Redis** | Fast in-memory store for caching and pub/sub |
| **MQTT** | Lightweight protocol ideal for IoT, QoS support |
| **React** | Component-based, large ecosystem, performance |
| **Docker** | Consistent environments, easy deployment, scalability |

## Future Enhancements

1. **Kubernetes Deployment** - Container orchestration for production
2. **GraphQL API** - Alternative to REST for flexible queries
3. **Edge Computing** - Data processing closer to devices
4. **Machine Learning Pipeline** - Automated model training and deployment
5. **Multi-tenancy** - Support for multiple organizations
6. **Mobile Apps** - Native iOS/Android applications
7. **Advanced Analytics** - Real-time dashboards with complex queries
8. **Integration Hub** - Pre-built connectors for third-party systems

---

**Document Version**: 1.0
**Last Updated**: 2024-01-15
**Author**: Platform Team
