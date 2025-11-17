from pydantic_settings import BaseSettings
from typing import List
from functools import lru_cache


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Smart City IoT Platform"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 0

    # InfluxDB
    INFLUXDB_URL: str = "http://localhost:8086"
    INFLUXDB_TOKEN: str
    INFLUXDB_ORG: str = "smartcity"
    INFLUXDB_BUCKET: str = "iot_sensors"

    # MQTT
    MQTT_BROKER_HOST: str = "localhost"
    MQTT_BROKER_PORT: int = 1883
    MQTT_USERNAME: str = "iot_platform"
    MQTT_PASSWORD: str
    MQTT_TOPIC_PREFIX: str = "smartcity"
    MQTT_QOS: int = 1

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 3600

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Security
    ALLOWED_HOSTS: str = "*"
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    DEVICE_TOKEN_EXPIRE_DAYS: int = 365

    # External APIs
    WEATHER_API_KEY: str = ""
    TRAFFIC_API_KEY: str = ""

    # Alerting
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    ALERT_EMAIL_FROM: str = ""

    # WebSocket
    WS_HOST: str = "0.0.0.0"
    WS_PORT: int = 8001

    # Monitoring
    PROMETHEUS_PORT: int = 9090

    # File Upload
    MAX_UPLOAD_SIZE: int = 10485760
    UPLOAD_DIR: str = "./uploads"

    # OTA
    FIRMWARE_STORAGE_PATH: str = "./firmware"
    MAX_FIRMWARE_SIZE: int = 52428800

    # ML
    ML_MODEL_PATH: str = "./ml_models"
    ENABLE_PREDICTIVE_ANALYTICS: bool = True

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    DEVICE_RATE_LIMIT_PER_MINUTE: int = 1000

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
