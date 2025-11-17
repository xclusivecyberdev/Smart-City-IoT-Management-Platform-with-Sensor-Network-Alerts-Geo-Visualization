# Deployment Guide - Smart City IoT Platform

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Development Deployment](#development-deployment)
3. [Production Deployment](#production-deployment)
4. [Cloud Deployment](#cloud-deployment)
5. [Security Hardening](#security-hardening)
6. [Monitoring Setup](#monitoring-setup)
7. [Backup & Recovery](#backup--recovery)
8. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

**Minimum Requirements** (Development):
- CPU: 4 cores
- RAM: 8 GB
- Storage: 50 GB SSD
- OS: Ubuntu 20.04 LTS, macOS, Windows 10 with WSL2

**Recommended Requirements** (Production):
- CPU: 8+ cores
- RAM: 32 GB
- Storage: 500 GB SSD (NVMe preferred)
- OS: Ubuntu 22.04 LTS

### Software Dependencies

```bash
# Docker & Docker Compose
Docker Engine 24.0+
Docker Compose 2.20+

# For local development
Python 3.11+
Node.js 18+
PostgreSQL 15+
```

## Development Deployment

### 1. Clone and Setup

```bash
# Clone repository
git clone <repository-url>
cd Smart-City-IoT-Management-Platform-with-Sensor-Network-Alerts-Geo-Visualization

# Copy environment file
cp .env.example .env

# Edit configuration
nano .env
```

### 2. Configure Environment Variables

```bash
# .env - Development Configuration
APP_NAME="Smart City IoT Platform"
ENVIRONMENT=development
DEBUG=true

# Database
DATABASE_URL=postgresql+asyncpg://smartcity:smartcity123@postgres:5432/smartcity_iot

# InfluxDB
INFLUXDB_URL=http://influxdb:8086
INFLUXDB_TOKEN=my-super-secret-influxdb-token
INFLUXDB_ORG=smartcity
INFLUXDB_BUCKET=iot_sensors

# MQTT
MQTT_BROKER_HOST=mosquitto
MQTT_USERNAME=iot_platform
MQTT_PASSWORD=mqtt_secure_pass

# Security (CHANGE IN PRODUCTION!)
SECRET_KEY=your-development-secret-key-change-in-production
```

### 3. Setup MQTT Broker

```bash
# Create Mosquitto password file
mkdir -p config/mosquitto
docker run -it --rm \
  -v $(pwd)/config/mosquitto:/mosquitto/config \
  eclipse-mosquitto:2 \
  mosquitto_passwd -c /mosquitto/config/passwd iot_platform
# Enter password: mqtt_secure_pass (or your chosen password)
```

### 4. Start Services

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Check service health
docker-compose ps
```

### 5. Initialize Database

```bash
# Wait for database to be ready (check logs)
docker-compose logs -f postgres

# Run migrations
docker-compose exec backend alembic upgrade head

# Create admin user
docker-compose exec backend python scripts/create_admin.py
```

### 6. Access Services

- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/api/docs
- **Grafana**: http://localhost:3001 (admin/admin)
- **InfluxDB**: http://localhost:8086

### 7. Test with Simulators

```bash
cd device-simulators
pip install -r requirements.txt

# Run simulators
./run_simulators.sh
```

## Production Deployment

### 1. Infrastructure Setup

#### Option A: Single Server Deployment

**Server Specifications**:
- 8 CPU cores
- 32 GB RAM
- 500 GB SSD
- Ubuntu 22.04 LTS
- Static IP address
- Domain name configured

**Initial Setup**:
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Create application user
sudo useradd -m -s /bin/bash smartcity
sudo usermod -aG docker smartcity
```

#### Option B: Multi-Server Deployment

```
┌─────────────────────┐
│  Load Balancer      │ (Nginx/HAProxy)
│  (Server 1)         │
└──────────┬──────────┘
           │
     ┌─────┴─────┐
     │           │
┌────▼─────┐ ┌──▼────────┐
│ App      │ │ App       │
│ Server 1 │ │ Server 2  │
└────┬─────┘ └──┬────────┘
     │          │
     └────┬─────┘
          │
┌─────────▼──────────┐
│  Database Cluster  │
│  (Primary/Replica) │
└────────────────────┘
```

### 2. Production Configuration

**Create production .env file**:
```bash
# Production environment
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING

# Strong passwords (use password generator)
DATABASE_URL=postgresql+asyncpg://smartcity:STRONG_PASSWORD@postgres:5432/smartcity_iot
INFLUXDB_TOKEN=STRONG_RANDOM_TOKEN_HERE
MQTT_PASSWORD=STRONG_MQTT_PASSWORD
SECRET_KEY=STRONG_JWT_SECRET_KEY_64_CHARS_MIN

# Redis with password
REDIS_URL=redis://:STRONG_REDIS_PASSWORD@redis:6379/0

# Email configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=alerts@yourdomain.com
SMTP_PASSWORD=your-app-password
ALERT_EMAIL_FROM=alerts@yourdomain.com

# Security
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# External APIs
WEATHER_API_KEY=your-weather-api-key
```

### 3. SSL/TLS Configuration

**Generate SSL certificates** (Let's Encrypt):
```bash
# Install certbot
sudo apt install certbot

# Generate certificates
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# Certificates will be in:
# /etc/letsencrypt/live/yourdomain.com/fullchain.pem
# /etc/letsencrypt/live/yourdomain.com/privkey.pem
```

**Configure Nginx** (`nginx/nginx.conf`):
```nginx
upstream backend {
    server backend:8000;
}

upstream frontend {
    server frontend:3000;
}

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Frontend
    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # API
    location /api {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket
    location /ws {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### 4. Docker Compose for Production

**Create `docker-compose.prod.yml`**:
```yaml
version: '3.8'

services:
  postgres:
    image: timescale/timescaledb:latest-pg15
    restart: always
    environment:
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    secrets:
      - db_password
    deploy:
      resources:
        limits:
          memory: 4G

  influxdb:
    image: influxdb:2.7
    restart: always
    volumes:
      - influxdb_data:/var/lib/influxdb2
    deploy:
      resources:
        limits:
          memory: 4G

  backend:
    build: ./backend
    restart: always
    depends_on:
      - postgres
      - influxdb
      - redis
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 2G

  # ... other services

volumes:
  postgres_data:
  influxdb_data:

secrets:
  db_password:
    file: ./secrets/db_password.txt
```

### 5. Deployment Steps

```bash
# 1. Transfer files to server
rsync -avz --exclude 'node_modules' --exclude '__pycache__' \
  ./ smartcity@server:/opt/smartcity/

# 2. SSH to server
ssh smartcity@server

# 3. Navigate to directory
cd /opt/smartcity

# 4. Setup secrets
mkdir -p secrets
echo "your-strong-db-password" > secrets/db_password.txt
chmod 600 secrets/*

# 5. Build and start services
docker-compose -f docker-compose.prod.yml up -d --build

# 6. Initialize database
docker-compose exec backend alembic upgrade head

# 7. Create admin user
docker-compose exec backend python scripts/create_admin.py

# 8. Check logs
docker-compose logs -f
```

## Cloud Deployment

### AWS Deployment

**Architecture**:
```
Route 53 → CloudFront → ALB → ECS/EC2
                              ↓
                        RDS (PostgreSQL)
                        ElastiCache (Redis)
                        InfluxDB Cloud
```

**Resources**:
- EC2: t3.xlarge (or ECS Fargate)
- RDS: db.r5.large (PostgreSQL 15)
- ElastiCache: cache.r5.large (Redis)
- S3: For firmware storage
- CloudWatch: Monitoring

**Deployment**:
```bash
# Using AWS CDK or Terraform
terraform init
terraform plan
terraform apply
```

### Azure Deployment

**Services**:
- Azure Container Instances (ACI) or AKS
- Azure Database for PostgreSQL
- Azure Cache for Redis
- Azure Storage (Blob)
- Application Insights

### Google Cloud Platform

**Services**:
- Google Kubernetes Engine (GKE)
- Cloud SQL (PostgreSQL)
- Memorystore (Redis)
- Cloud Storage
- Cloud Monitoring

## Security Hardening

### 1. Firewall Configuration

```bash
# UFW (Ubuntu Firewall)
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw allow 8883/tcp # MQTT over TLS
sudo ufw enable
```

### 2. MQTT Security

**Enable TLS in Mosquitto**:
```conf
# mosquitto.conf
listener 8883
protocol mqtt
cafile /mosquitto/certs/ca.crt
certfile /mosquitto/certs/server.crt
keyfile /mosquitto/certs/server.key
require_certificate true
```

### 3. Database Security

```bash
# PostgreSQL - pg_hba.conf
hostssl all all 0.0.0.0/0 scram-sha-256

# Encryption at rest
# Enable in postgresql.conf
ssl = on
ssl_cert_file = 'server.crt'
ssl_key_file = 'server.key'
```

### 4. Secrets Management

**Using Docker Secrets**:
```yaml
secrets:
  db_password:
    external: true
  jwt_secret:
    external: true
```

**Or use HashiCorp Vault**:
```bash
vault kv put secret/smartcity \
  db_password="..." \
  jwt_secret="..."
```

## Monitoring Setup

### Prometheus Configuration

**prometheus.yml**:
```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'backend'
    static_configs:
      - targets: ['backend:8000']

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']
```

### Grafana Dashboards

Import pre-built dashboards:
1. Grafana.com ID: 11074 (PostgreSQL)
2. Grafana.com ID: 763 (Redis)
3. Custom dashboard for application metrics

### Alerting

**Configure Alertmanager**:
```yaml
route:
  receiver: 'team-alerts'

receivers:
  - name: 'team-alerts'
    email_configs:
      - to: 'ops@yourdomain.com'
    slack_configs:
      - api_url: 'YOUR_SLACK_WEBHOOK'
        channel: '#alerts'
```

## Backup & Recovery

### Automated Backups

**PostgreSQL**:
```bash
#!/bin/bash
# backup-postgres.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/postgres"

docker-compose exec -T postgres pg_dump -U smartcity smartcity_iot | \
  gzip > "$BACKUP_DIR/backup_$DATE.sql.gz"

# Keep only last 30 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete

# Upload to S3
aws s3 cp "$BACKUP_DIR/backup_$DATE.sql.gz" \
  s3://smartcity-backups/postgres/
```

**InfluxDB**:
```bash
#!/bin/bash
# backup-influxdb.sh

influx backup /backups/influxdb/$(date +%Y%m%d)
```

**Cron Job**:
```bash
# Daily backups at 2 AM
0 2 * * * /opt/smartcity/scripts/backup-postgres.sh
0 3 * * * /opt/smartcity/scripts/backup-influxdb.sh
```

### Restore Procedures

**PostgreSQL Restore**:
```bash
gunzip -c backup_20240115.sql.gz | \
  docker-compose exec -T postgres psql -U smartcity smartcity_iot
```

## Troubleshooting

### Common Issues

**1. Database Connection Failures**
```bash
# Check database is running
docker-compose ps postgres

# Check logs
docker-compose logs postgres

# Test connection
docker-compose exec postgres psql -U smartcity -d smartcity_iot -c "SELECT 1;"
```

**2. MQTT Connection Issues**
```bash
# Test MQTT broker
mosquitto_sub -h localhost -p 1883 -t "test" -u iot_platform -P mqtt_secure_pass

# Check broker logs
docker-compose logs mosquitto
```

**3. High Memory Usage**
```bash
# Check container resources
docker stats

# Increase limits in docker-compose.yml
deploy:
  resources:
    limits:
      memory: 4G
```

**4. API Performance Issues**
```bash
# Enable query logging
LOG_LEVEL=DEBUG

# Check slow queries in PostgreSQL
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
```

### Health Checks

```bash
# Check all services
curl http://localhost:8000/health

# Check database
curl http://localhost:8000/health/db

# Check MQTT
curl http://localhost:8000/health/mqtt
```

### Logs

```bash
# View all logs
docker-compose logs -f

# Filter by service
docker-compose logs -f backend

# Export logs
docker-compose logs > logs_$(date +%Y%m%d).txt
```

## Maintenance

### Updates

```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose up -d --build

# Run migrations
docker-compose exec backend alembic upgrade head
```

### Database Maintenance

```bash
# Vacuum PostgreSQL
docker-compose exec postgres vacuumdb -U smartcity -d smartcity_iot --analyze

# Reindex
docker-compose exec postgres reindexdb -U smartcity -d smartcity_iot
```

---

**Document Version**: 1.0
**Last Updated**: 2024-01-15
