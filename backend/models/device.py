from sqlalchemy import Column, String, Float, Integer, DateTime, Boolean, JSON, Enum as SQLEnum, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum
from ..core.database import Base


class DeviceType(str, enum.Enum):
    TRAFFIC_SENSOR = "traffic_sensor"
    POLLUTION_MONITOR = "pollution_monitor"
    PARKING_METER = "parking_meter"
    WATER_LEVEL_SENSOR = "water_level_sensor"
    GARBAGE_BIN_SENSOR = "garbage_bin_sensor"
    ENERGY_METER = "energy_meter"
    WEATHER_STATION = "weather_station"
    PUBLIC_SAFETY_DEVICE = "public_safety_device"


class DeviceStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    OFFLINE = "offline"
    ERROR = "error"


class Device(Base):
    __tablename__ = "devices"

    id = Column(String(100), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    device_type = Column(SQLEnum(DeviceType), nullable=False, index=True)
    status = Column(SQLEnum(DeviceStatus), default=DeviceStatus.ACTIVE, index=True)

    # Authentication
    api_key_hash = Column(String(255), nullable=True)
    certificate_fingerprint = Column(String(255), nullable=True, unique=True)

    # Location
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    address = Column(Text, nullable=True)
    zone = Column(String(100), nullable=True, index=True)

    # Firmware & Configuration
    firmware_version = Column(String(50), nullable=True)
    hardware_version = Column(String(50), nullable=True)
    configuration = Column(JSON, default={})

    # Metadata
    manufacturer = Column(String(100), nullable=True)
    model = Column(String(100), nullable=True)
    serial_number = Column(String(100), nullable=True, unique=True)
    installation_date = Column(DateTime, nullable=True)

    # Status tracking
    last_seen = Column(DateTime, nullable=True)
    last_data_received = Column(DateTime, nullable=True)
    battery_level = Column(Float, nullable=True)
    signal_strength = Column(Integer, nullable=True)

    # Sampling configuration
    sampling_rate_seconds = Column(Integer, default=60)

    # Ownership
    owner_id = Column(String(100), ForeignKey("users.id"), nullable=True)

    # Audit
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(String(100), nullable=True)

    # Additional metadata
    metadata = Column(JSON, default={})
    tags = Column(JSON, default=[])

    # Relationships
    owner = relationship("User", back_populates="devices")
    alerts = relationship("Alert", back_populates="device", cascade="all, delete-orphan")
    maintenance_logs = relationship("MaintenanceLog", back_populates="device", cascade="all, delete-orphan")
    firmware_updates = relationship("FirmwareUpdate", back_populates="device", cascade="all, delete-orphan")


class FirmwareUpdate(Base):
    __tablename__ = "firmware_updates"

    id = Column(String(100), primary_key=True, index=True)
    device_id = Column(String(100), ForeignKey("devices.id"), nullable=False, index=True)

    from_version = Column(String(50), nullable=True)
    to_version = Column(String(50), nullable=False)

    status = Column(String(50), default="pending")  # pending, in_progress, completed, failed
    firmware_url = Column(Text, nullable=True)
    checksum = Column(String(255), nullable=True)

    scheduled_at = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    created_by = Column(String(100), nullable=True)

    # Relationships
    device = relationship("Device", back_populates="firmware_updates")


class MaintenanceLog(Base):
    __tablename__ = "maintenance_logs"

    id = Column(String(100), primary_key=True, index=True)
    device_id = Column(String(100), ForeignKey("devices.id"), nullable=False, index=True)

    maintenance_type = Column(String(50), nullable=False)  # repair, inspection, calibration, replacement
    description = Column(Text, nullable=False)

    technician_id = Column(String(100), ForeignKey("users.id"), nullable=True)

    scheduled_at = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    status = Column(String(50), default="scheduled")  # scheduled, in_progress, completed, cancelled

    notes = Column(Text, nullable=True)
    parts_replaced = Column(JSON, default=[])
    cost = Column(Float, nullable=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    created_by = Column(String(100), nullable=True)

    # Relationships
    device = relationship("Device", back_populates="maintenance_logs")
    technician = relationship("User", foreign_keys=[technician_id])
