from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from typing import List, Optional
import uuid
from datetime import datetime

from ..core.database import get_db
from ..core.security import get_current_user, verify_device_token, RoleChecker, generate_device_api_key, hash_api_key
from ..models.device import Device, DeviceType, DeviceStatus
from ..models.user import User, UserRole
from ..schemas.device import (
    DeviceCreate, DeviceUpdate, DeviceResponse, DeviceListResponse,
    SensorData, SensorDataBatch
)
from ..services.influxdb import influxdb_service
from ..services.mqtt_service import mqtt_service

router = APIRouter()


@router.post("/devices", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
async def create_device(
    device_data: DeviceCreate,
    current_user: User = Depends(RoleChecker([UserRole.ADMIN, UserRole.ENGINEER])),
    db: AsyncSession = Depends(get_db)
):
    """Create a new IoT device"""
    # Check if device already exists
    result = await db.execute(select(Device).where(Device.id == device_data.id))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Device ID already exists")

    # Generate API key if not provided
    api_key = None
    api_key_hash = None
    if device_data.api_key:
        api_key_hash = hash_api_key(device_data.api_key)
    elif not device_data.certificate_fingerprint:
        # Generate API key if no certificate provided
        api_key = generate_device_api_key()
        api_key_hash = hash_api_key(api_key)

    # Create device
    device = Device(
        id=device_data.id,
        name=device_data.name,
        device_type=device_data.device_type,
        latitude=device_data.latitude,
        longitude=device_data.longitude,
        address=device_data.address,
        zone=device_data.zone,
        api_key_hash=api_key_hash,
        certificate_fingerprint=device_data.certificate_fingerprint,
        firmware_version=device_data.firmware_version,
        hardware_version=device_data.hardware_version,
        manufacturer=device_data.manufacturer,
        model=device_data.model,
        serial_number=device_data.serial_number,
        installation_date=device_data.installation_date,
        sampling_rate_seconds=device_data.sampling_rate_seconds,
        configuration=device_data.configuration,
        metadata=device_data.metadata,
        tags=device_data.tags,
        owner_id=current_user.id,
        created_by=current_user.id
    )

    db.add(device)
    await db.commit()
    await db.refresh(device)

    # Return device with API key (only shown once)
    response = DeviceResponse.from_orm(device)
    if api_key:
        response.metadata['api_key'] = api_key

    return response


@router.get("/devices", response_model=DeviceListResponse)
async def list_devices(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    device_type: Optional[DeviceType] = None,
    status: Optional[DeviceStatus] = None,
    zone: Optional[str] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all devices with filtering and pagination"""
    query = select(Device)

    # Apply filters
    filters = []
    if device_type:
        filters.append(Device.device_type == device_type)
    if status:
        filters.append(Device.status == status)
    if zone:
        filters.append(Device.zone == zone)
    if search:
        filters.append(
            or_(
                Device.name.ilike(f"%{search}%"),
                Device.id.ilike(f"%{search}%")
            )
        )

    if filters:
        query = query.where(and_(*filters))

    # Get total count
    count_query = select(func.count()).select_from(Device)
    if filters:
        count_query = count_query.where(and_(*filters))
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    # Execute query
    result = await db.execute(query)
    devices = result.scalars().all()

    return DeviceListResponse(
        devices=[DeviceResponse.from_orm(d) for d in devices],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/devices/{device_id}", response_model=DeviceResponse)
async def get_device(
    device_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get device by ID"""
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    return DeviceResponse.from_orm(device)


@router.put("/devices/{device_id}", response_model=DeviceResponse)
async def update_device(
    device_id: str,
    device_data: DeviceUpdate,
    current_user: User = Depends(RoleChecker([UserRole.ADMIN, UserRole.ENGINEER])),
    db: AsyncSession = Depends(get_db)
):
    """Update device information"""
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    # Update fields
    update_data = device_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(device, field, value)

    await db.commit()
    await db.refresh(device)

    return DeviceResponse.from_orm(device)


@router.delete("/devices/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_device(
    device_id: str,
    current_user: User = Depends(RoleChecker([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """Delete a device"""
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    await db.delete(device)
    await db.commit()


@router.post("/devices/{device_id}/data", status_code=status.HTTP_201_CREATED)
async def ingest_sensor_data(
    device_id: str,
    sensor_data: SensorData,
    device: Device = Depends(verify_device_token),
    db: AsyncSession = Depends(get_db)
):
    """Ingest sensor data from device (REST endpoint)"""
    # Verify device ID matches
    if device.id != device_id:
        raise HTTPException(status_code=403, detail="Device ID mismatch")

    # Update device last_seen
    device.last_seen = datetime.utcnow()
    device.last_data_received = datetime.utcnow()

    # Write to InfluxDB
    influxdb_service.write_sensor_data(
        device_id=device_id,
        device_type=device.device_type.value,
        data=sensor_data.data,
        timestamp=sensor_data.timestamp
    )

    await db.commit()

    return {"status": "success", "message": "Data ingested successfully"}


@router.post("/devices/{device_id}/data/batch", status_code=status.HTTP_201_CREATED)
async def ingest_sensor_data_batch(
    device_id: str,
    batch_data: SensorDataBatch,
    device: Device = Depends(verify_device_token),
    db: AsyncSession = Depends(get_db)
):
    """Ingest batch sensor data from device"""
    if device.id != device_id:
        raise HTTPException(status_code=403, detail="Device ID mismatch")

    # Update device last_seen
    device.last_seen = datetime.utcnow()
    device.last_data_received = datetime.utcnow()

    # Write batch to InfluxDB
    influxdb_service.write_batch_sensor_data(
        device_id=device_id,
        device_type=device.device_type.value,
        data_points=batch_data.data_points
    )

    await db.commit()

    return {
        "status": "success",
        "message": f"Batch of {len(batch_data.data_points)} data points ingested"
    }


@router.get("/devices/{device_id}/data")
async def get_device_data(
    device_id: str,
    start_time: str = Query("-1h", description="Start time (e.g., -1h, -24h)"),
    stop_time: str = Query("now()", description="Stop time"),
    current_user: User = Depends(get_current_user)
):
    """Get historical sensor data for a device"""
    try:
        data_points = influxdb_service.query_device_data(
            device_id=device_id,
            start_time=start_time,
            stop_time=stop_time
        )

        return {
            "device_id": device_id,
            "start_time": start_time,
            "stop_time": stop_time,
            "data_points": data_points,
            "count": len(data_points)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
