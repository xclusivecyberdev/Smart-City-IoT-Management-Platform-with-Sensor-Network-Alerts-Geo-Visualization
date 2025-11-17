from sqlalchemy import Column, String, Float, Integer, DateTime, Boolean, JSON, Enum as SQLEnum, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from ..core.database import Base


class AlertSeverity(str, enum.Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class AlertStatus(str, enum.Enum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    CLOSED = "closed"


class AlertType(str, enum.Enum):
    HIGH_POLLUTION = "high_pollution"
    TRAFFIC_CONGESTION = "traffic_congestion"
    OVERFLOW_GARBAGE = "overflow_garbage"
    WATER_LEVEL_HIGH = "water_level_high"
    INFRASTRUCTURE_FAILURE = "infrastructure_failure"
    DEVICE_OFFLINE = "device_offline"
    LOW_BATTERY = "low_battery"
    ANOMALY_DETECTED = "anomaly_detected"
    THRESHOLD_BREACH = "threshold_breach"


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(String(100), primary_key=True, index=True)
    device_id = Column(String(100), ForeignKey("devices.id"), nullable=False, index=True)
    rule_id = Column(String(100), ForeignKey("alert_rules.id"), nullable=True, index=True)

    alert_type = Column(SQLEnum(AlertType), nullable=False, index=True)
    severity = Column(SQLEnum(AlertSeverity), nullable=False, index=True)
    status = Column(SQLEnum(AlertStatus), default=AlertStatus.OPEN, nullable=False, index=True)

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Alert data
    value = Column(Float, nullable=True)
    threshold = Column(Float, nullable=True)
    unit = Column(String(50), nullable=True)

    # Geolocation (denormalized for quick access)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    # Timestamps
    triggered_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)
    acknowledged_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)

    # Acknowledgment/Resolution
    acknowledged_by = Column(String(100), nullable=True)
    resolved_by = Column(String(100), nullable=True)
    resolution_notes = Column(Text, nullable=True)

    # Notification tracking
    notifications_sent = Column(JSON, default=[])
    notification_channels = Column(JSON, default=[])

    # Additional data
    metadata = Column(JSON, default={})

    # Relationships
    device = relationship("Device", back_populates="alerts")
    rule = relationship("AlertRule", back_populates="alerts")


class AlertRule(Base):
    __tablename__ = "alert_rules"

    id = Column(String(100), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Rule conditions
    device_type = Column(String(50), nullable=True, index=True)
    metric_name = Column(String(100), nullable=False)

    condition = Column(String(50), nullable=False)  # gt, lt, eq, gte, lte, between
    threshold_value = Column(Float, nullable=True)
    threshold_min = Column(Float, nullable=True)
    threshold_max = Column(Float, nullable=True)

    # Rule configuration
    severity = Column(SQLEnum(AlertSeverity), nullable=False)
    alert_type = Column(SQLEnum(AlertType), nullable=False)

    # Time window for evaluation
    time_window_minutes = Column(Integer, default=5)
    evaluation_interval_seconds = Column(Integer, default=60)

    # Notification settings
    notification_channels = Column(JSON, default=["email"])  # email, sms, webhook, push
    notification_recipients = Column(JSON, default=[])

    # Suppression
    suppression_enabled = Column(Boolean, default=False)
    suppression_minutes = Column(Integer, default=30)

    # Rule status
    is_enabled = Column(Boolean, default=True, nullable=False)

    # Geofencing (optional)
    geo_fence_enabled = Column(Boolean, default=False)
    geo_fence_center_lat = Column(Float, nullable=True)
    geo_fence_center_lon = Column(Float, nullable=True)
    geo_fence_radius_meters = Column(Float, nullable=True)

    # Audit
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(String(100), nullable=True)

    # Additional conditions (JSON for complex rules)
    conditions = Column(JSON, default={})

    # Relationships
    alerts = relationship("Alert", back_populates="rule")
