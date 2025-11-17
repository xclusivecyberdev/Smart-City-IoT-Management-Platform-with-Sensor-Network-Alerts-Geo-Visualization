from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, List, Any
from datetime import datetime
from ..models.device import DeviceType, DeviceStatus


class DeviceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    device_type: DeviceType
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    address: Optional[str] = None
    zone: Optional[str] = None


class DeviceCreate(DeviceBase):
    id: str = Field(..., min_length=1, max_length=100)
    api_key: Optional[str] = None
    certificate_fingerprint: Optional[str] = None
    firmware_version: Optional[str] = None
    hardware_version: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    installation_date: Optional[datetime] = None
    sampling_rate_seconds: int = Field(default=60, ge=1)
    configuration: Optional[Dict[str, Any]] = {}
    metadata: Optional[Dict[str, Any]] = {}
    tags: Optional[List[str]] = []


class DeviceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    status: Optional[DeviceStatus] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    address: Optional[str] = None
    zone: Optional[str] = None
    firmware_version: Optional[str] = None
    configuration: Optional[Dict[str, Any]] = None
    sampling_rate_seconds: Optional[int] = Field(None, ge=1)
    metadata: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None


class DeviceResponse(DeviceBase):
    id: str
    status: DeviceStatus
    firmware_version: Optional[str]
    hardware_version: Optional[str]
    configuration: Dict[str, Any]
    manufacturer: Optional[str]
    model: Optional[str]
    serial_number: Optional[str]
    installation_date: Optional[datetime]
    last_seen: Optional[datetime]
    last_data_received: Optional[datetime]
    battery_level: Optional[float]
    signal_strength: Optional[int]
    sampling_rate_seconds: int
    owner_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]
    tags: List[str]

    class Config:
        from_attributes = True


class DeviceListResponse(BaseModel):
    devices: List[DeviceResponse]
    total: int
    page: int
    page_size: int


class SensorData(BaseModel):
    device_id: str
    timestamp: datetime
    data: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = {}


class SensorDataBatch(BaseModel):
    device_id: str
    data_points: List[Dict[str, Any]]


class FirmwareUpdateCreate(BaseModel):
    device_ids: List[str]
    to_version: str
    firmware_url: str
    checksum: str
    scheduled_at: Optional[datetime] = None


class FirmwareUpdateResponse(BaseModel):
    id: str
    device_id: str
    from_version: Optional[str]
    to_version: str
    status: str
    firmware_url: Optional[str]
    scheduled_at: Optional[datetime]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class MaintenanceLogCreate(BaseModel):
    device_id: str
    maintenance_type: str
    description: str
    scheduled_at: Optional[datetime] = None
    notes: Optional[str] = None
    parts_replaced: Optional[List[Dict[str, Any]]] = []
    cost: Optional[float] = None


class MaintenanceLogResponse(BaseModel):
    id: str
    device_id: str
    maintenance_type: str
    description: str
    technician_id: Optional[str]
    scheduled_at: Optional[datetime]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    status: str
    notes: Optional[str]
    parts_replaced: List[Dict[str, Any]]
    cost: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True


class DeviceCommand(BaseModel):
    command: str  # restart, update_config, update_sampling_rate
    parameters: Optional[Dict[str, Any]] = {}
    device_ids: List[str]
