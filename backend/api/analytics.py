from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import Optional, List
from datetime import datetime, timedelta

from ..core.database import get_db
from ..core.security import get_current_user
from ..models.device import Device, DeviceType, DeviceStatus
from ..models.alert import Alert, AlertSeverity
from ..models.user import User
from ..services.influxdb import influxdb_service

router = APIRouter()


@router.get("/analytics/dashboard/summary")
async def get_dashboard_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get dashboard summary statistics"""
    # Device counts
    total_devices_result = await db.execute(select(func.count()).select_from(Device))
    total_devices = total_devices_result.scalar()

    active_devices_result = await db.execute(
        select(func.count()).select_from(Device).where(Device.status == DeviceStatus.ACTIVE)
    )
    active_devices = active_devices_result.scalar()

    offline_devices_result = await db.execute(
        select(func.count()).select_from(Device).where(Device.status == DeviceStatus.OFFLINE)
    )
    offline_devices = offline_devices_result.scalar()

    # Device counts by type
    device_counts_by_type = {}
    for device_type in DeviceType:
        result = await db.execute(
            select(func.count()).select_from(Device).where(Device.device_type == device_type)
        )
        device_counts_by_type[device_type.value] = result.scalar()

    # Active alerts
    active_alerts_result = await db.execute(
        select(func.count()).select_from(Alert).where(
            Alert.status.in_(['open', 'acknowledged'])
        )
    )
    active_alerts = active_alerts_result.scalar()

    # Critical alerts
    critical_alerts_result = await db.execute(
        select(func.count()).select_from(Alert).where(
            and_(
                Alert.status == 'open',
                Alert.severity == AlertSeverity.CRITICAL
            )
        )
    )
    critical_alerts = critical_alerts_result.scalar()

    return {
        "devices": {
            "total": total_devices,
            "active": active_devices,
            "offline": offline_devices,
            "by_type": device_counts_by_type
        },
        "alerts": {
            "active": active_alerts,
            "critical": critical_alerts
        }
    }


@router.get("/analytics/devices/map")
async def get_devices_map_data(
    device_type: Optional[DeviceType] = None,
    status: Optional[DeviceStatus] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get device locations for map visualization"""
    query = select(Device)

    filters = []
    if device_type:
        filters.append(Device.device_type == device_type)
    if status:
        filters.append(Device.status == status)

    if filters:
        query = query.where(and_(*filters))

    result = await db.execute(query)
    devices = result.scalars().all()

    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [device.longitude, device.latitude]
                },
                "properties": {
                    "id": device.id,
                    "name": device.name,
                    "device_type": device.device_type.value,
                    "status": device.status.value,
                    "zone": device.zone,
                    "last_seen": device.last_seen.isoformat() if device.last_seen else None,
                    "battery_level": device.battery_level,
                    "signal_strength": device.signal_strength
                }
            }
            for device in devices
        ]
    }


@router.get("/analytics/time-series/{device_type}/{metric}")
async def get_time_series_data(
    device_type: str,
    metric: str,
    aggregation: str = Query("mean", regex="^(mean|sum|min|max|count)$"),
    window: str = Query("1h", description="Aggregation window (e.g., 1h, 15m)"),
    start_time: str = Query("-24h", description="Start time"),
    current_user: User = Depends(get_current_user)
):
    """Get aggregated time-series data for a device type and metric"""
    try:
        data_points = influxdb_service.query_aggregated_data(
            device_type=device_type,
            field=metric,
            aggregation=aggregation,
            window=window,
            start_time=start_time
        )

        return {
            "device_type": device_type,
            "metric": metric,
            "aggregation": aggregation,
            "window": window,
            "start_time": start_time,
            "data_points": data_points,
            "count": len(data_points)
        }

    except Exception as e:
        return {"error": str(e)}


@router.get("/analytics/pollution/trends")
async def get_pollution_trends(
    start_time: str = Query("-30d", description="Start time"),
    window: str = Query("1d", description="Aggregation window"),
    current_user: User = Depends(get_current_user)
):
    """Get pollution trends over time"""
    try:
        # Query multiple pollution metrics
        metrics = ["pm25", "pm10", "no2", "co2", "o3"]
        trends = {}

        for metric in metrics:
            data_points = influxdb_service.query_aggregated_data(
                device_type="pollution_monitor",
                field=metric,
                aggregation="mean",
                window=window,
                start_time=start_time
            )
            trends[metric] = data_points

        return {
            "start_time": start_time,
            "window": window,
            "trends": trends
        }

    except Exception as e:
        return {"error": str(e)}


@router.get("/analytics/traffic/congestion")
async def get_traffic_congestion(
    zone: Optional[str] = None,
    start_time: str = Query("-24h"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get traffic congestion analytics"""
    try:
        # Get traffic sensors in specified zone
        query = select(Device).where(Device.device_type == DeviceType.TRAFFIC_SENSOR)
        if zone:
            query = query.where(Device.zone == zone)

        result = await db.execute(query)
        devices = result.scalars().all()

        congestion_data = []

        for device in devices:
            device_data = influxdb_service.query_device_data(
                device_id=device.id,
                start_time=start_time
            )

            congestion_data.append({
                "device_id": device.id,
                "device_name": device.name,
                "zone": device.zone,
                "latitude": device.latitude,
                "longitude": device.longitude,
                "data": device_data
            })

        return {
            "zone": zone,
            "start_time": start_time,
            "congestion_data": congestion_data
        }

    except Exception as e:
        return {"error": str(e)}


@router.get("/analytics/energy/consumption")
async def get_energy_consumption(
    zone: Optional[str] = None,
    start_time: str = Query("-7d"),
    window: str = Query("1h"),
    current_user: User = Depends(get_current_user)
):
    """Get energy consumption analytics"""
    try:
        data_points = influxdb_service.query_aggregated_data(
            device_type="energy_meter",
            field="power_consumption",
            aggregation="sum",
            window=window,
            start_time=start_time
        )

        return {
            "zone": zone,
            "start_time": start_time,
            "window": window,
            "total_consumption": sum(d['value'] for d in data_points if d['value']),
            "data_points": data_points
        }

    except Exception as e:
        return {"error": str(e)}


@router.get("/analytics/weather/metrics")
async def get_weather_metrics(
    start_time: str = Query("-7d"),
    window: str = Query("1h"),
    current_user: User = Depends(get_current_user)
):
    """Get weather station metrics"""
    try:
        metrics = ["temperature", "humidity", "pressure", "wind_speed", "rainfall"]
        weather_data = {}

        for metric in metrics:
            data_points = influxdb_service.query_aggregated_data(
                device_type="weather_station",
                field=metric,
                aggregation="mean",
                window=window,
                start_time=start_time
            )
            weather_data[metric] = data_points

        return {
            "start_time": start_time,
            "window": window,
            "metrics": weather_data
        }

    except Exception as e:
        return {"error": str(e)}


@router.get("/analytics/zones/statistics")
async def get_zone_statistics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get statistics by zone"""
    # Get all unique zones
    result = await db.execute(
        select(Device.zone, func.count()).group_by(Device.zone).where(Device.zone.isnot(None))
    )
    zones_data = result.all()

    zone_stats = []
    for zone, device_count in zones_data:
        # Count alerts in this zone
        alert_result = await db.execute(
            select(func.count()).select_from(Alert)
            .join(Device, Alert.device_id == Device.id)
            .where(and_(Device.zone == zone, Alert.status == 'open'))
        )
        alert_count = alert_result.scalar()

        zone_stats.append({
            "zone": zone,
            "device_count": device_count,
            "active_alerts": alert_count
        })

    return {"zones": zone_stats}
