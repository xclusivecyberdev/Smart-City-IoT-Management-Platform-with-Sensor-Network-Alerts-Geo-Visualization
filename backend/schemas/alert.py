from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from ..models.alert import AlertSeverity, AlertStatus, AlertType


class AlertRuleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    device_type: Optional[str] = None
    metric_name: str
    condition: str = Field(..., pattern="^(gt|lt|eq|gte|lte|between)$")
    severity: AlertSeverity
    alert_type: AlertType


class AlertRuleCreate(AlertRuleBase):
    threshold_value: Optional[float] = None
    threshold_min: Optional[float] = None
    threshold_max: Optional[float] = None
    time_window_minutes: int = Field(default=5, ge=1)
    evaluation_interval_seconds: int = Field(default=60, ge=10)
    notification_channels: List[str] = ["email"]
    notification_recipients: List[str] = []
    suppression_enabled: bool = False
    suppression_minutes: int = 30
    is_enabled: bool = True
    geo_fence_enabled: bool = False
    geo_fence_center_lat: Optional[float] = None
    geo_fence_center_lon: Optional[float] = None
    geo_fence_radius_meters: Optional[float] = None
    conditions: Optional[Dict[str, Any]] = {}


class AlertRuleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    threshold_value: Optional[float] = None
    threshold_min: Optional[float] = None
    threshold_max: Optional[float] = None
    notification_channels: Optional[List[str]] = None
    notification_recipients: Optional[List[str]] = None
    is_enabled: Optional[bool] = None
    conditions: Optional[Dict[str, Any]] = None


class AlertRuleResponse(AlertRuleBase):
    id: str
    threshold_value: Optional[float]
    threshold_min: Optional[float]
    threshold_max: Optional[float]
    time_window_minutes: int
    evaluation_interval_seconds: int
    notification_channels: List[str]
    notification_recipients: List[str]
    suppression_enabled: bool
    suppression_minutes: int
    is_enabled: bool
    geo_fence_enabled: bool
    geo_fence_center_lat: Optional[float]
    geo_fence_center_lon: Optional[float]
    geo_fence_radius_meters: Optional[float]
    conditions: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AlertResponse(BaseModel):
    id: str
    device_id: str
    rule_id: Optional[str]
    alert_type: AlertType
    severity: AlertSeverity
    status: AlertStatus
    title: str
    description: Optional[str]
    value: Optional[float]
    threshold: Optional[float]
    unit: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    triggered_at: datetime
    acknowledged_at: Optional[datetime]
    resolved_at: Optional[datetime]
    closed_at: Optional[datetime]
    acknowledged_by: Optional[str]
    resolved_by: Optional[str]
    resolution_notes: Optional[str]
    notifications_sent: List[Any]
    notification_channels: List[str]
    metadata: Dict[str, Any]

    class Config:
        from_attributes = True


class AlertAcknowledge(BaseModel):
    notes: Optional[str] = None


class AlertResolve(BaseModel):
    resolution_notes: str


class AlertListResponse(BaseModel):
    alerts: List[AlertResponse]
    total: int
    page: int
    page_size: int
