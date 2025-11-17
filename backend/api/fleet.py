from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List
import uuid
from datetime import datetime

from ..core.database import get_db
from ..core.security import get_current_user, RoleChecker
from ..models.device import Device, FirmwareUpdate, MaintenanceLog
from ..models.user import User, UserRole
from ..schemas.device import (
    DeviceCommand, FirmwareUpdateCreate, FirmwareUpdateResponse,
    MaintenanceLogCreate, MaintenanceLogResponse
)
from ..services.mqtt_service import mqtt_service

router = APIRouter()


@router.post("/fleet/commands")
async def send_fleet_command(
    command_data: DeviceCommand,
    current_user: User = Depends(RoleChecker([UserRole.ADMIN, UserRole.ENGINEER])),
    db: AsyncSession = Depends(get_db)
):
    """Send command to multiple devices"""
    # Verify devices exist
    result = await db.execute(
        select(Device).where(Device.id.in_(command_data.device_ids))
    )
    devices = result.scalars().all()

    if len(devices) != len(command_data.device_ids):
        raise HTTPException(status_code=404, detail="Some devices not found")

    # Send command via MQTT to each device
    success_count = 0
    failed_devices = []

    for device_id in command_data.device_ids:
        success = mqtt_service.send_command_to_device(
            device_id=device_id,
            command=command_data.command,
            parameters=command_data.parameters
        )

        if success:
            success_count += 1
        else:
            failed_devices.append(device_id)

    return {
        "command": command_data.command,
        "total_devices": len(command_data.device_ids),
        "success_count": success_count,
        "failed_count": len(failed_devices),
        "failed_devices": failed_devices
    }


@router.post("/fleet/broadcast/{device_type}")
async def broadcast_command(
    device_type: str,
    command: str,
    parameters: dict = {},
    current_user: User = Depends(RoleChecker([UserRole.ADMIN, UserRole.ENGINEER])),
):
    """Broadcast command to all devices of a specific type"""
    success = mqtt_service.broadcast_command(
        device_type=device_type,
        command=command,
        parameters=parameters
    )

    if not success:
        raise HTTPException(status_code=500, detail="Failed to broadcast command")

    return {
        "message": f"Command '{command}' broadcast to all {device_type} devices",
        "device_type": device_type,
        "command": command
    }


# Firmware Updates
@router.post("/fleet/firmware-updates", response_model=List[FirmwareUpdateResponse])
async def create_firmware_update(
    update_data: FirmwareUpdateCreate,
    current_user: User = Depends(RoleChecker([UserRole.ADMIN, UserRole.ENGINEER])),
    db: AsyncSession = Depends(get_db)
):
    """Schedule firmware updates for devices"""
    # Verify devices exist
    result = await db.execute(
        select(Device).where(Device.id.in_(update_data.device_ids))
    )
    devices = result.scalars().all()

    if len(devices) != len(update_data.device_ids):
        raise HTTPException(status_code=404, detail="Some devices not found")

    # Create firmware update records
    updates = []
    for device in devices:
        firmware_update = FirmwareUpdate(
            id=str(uuid.uuid4()),
            device_id=device.id,
            from_version=device.firmware_version,
            to_version=update_data.to_version,
            firmware_url=update_data.firmware_url,
            checksum=update_data.checksum,
            scheduled_at=update_data.scheduled_at,
            status="pending",
            created_by=current_user.id
        )

        db.add(firmware_update)
        updates.append(firmware_update)

    await db.commit()

    # Send OTA update command via MQTT
    for device in devices:
        mqtt_service.send_command_to_device(
            device_id=device.id,
            command="ota_update",
            parameters={
                "firmware_url": update_data.firmware_url,
                "version": update_data.to_version,
                "checksum": update_data.checksum,
                "scheduled_at": update_data.scheduled_at.isoformat() if update_data.scheduled_at else None
            }
        )

    return [FirmwareUpdateResponse.from_orm(u) for u in updates]


@router.get("/fleet/firmware-updates", response_model=List[FirmwareUpdateResponse])
async def list_firmware_updates(
    device_id: str = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List firmware updates"""
    query = select(FirmwareUpdate).order_by(FirmwareUpdate.created_at.desc())

    if device_id:
        query = query.where(FirmwareUpdate.device_id == device_id)

    result = await db.execute(query)
    updates = result.scalars().all()

    return [FirmwareUpdateResponse.from_orm(u) for u in updates]


@router.get("/fleet/firmware-updates/{update_id}", response_model=FirmwareUpdateResponse)
async def get_firmware_update(
    update_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get firmware update by ID"""
    result = await db.execute(
        select(FirmwareUpdate).where(FirmwareUpdate.id == update_id)
    )
    update = result.scalar_one_or_none()

    if not update:
        raise HTTPException(status_code=404, detail="Firmware update not found")

    return FirmwareUpdateResponse.from_orm(update)


# Maintenance Logs
@router.post("/fleet/maintenance", response_model=MaintenanceLogResponse)
async def create_maintenance_log(
    log_data: MaintenanceLogCreate,
    current_user: User = Depends(RoleChecker([UserRole.ADMIN, UserRole.ENGINEER])),
    db: AsyncSession = Depends(get_db)
):
    """Create maintenance log for a device"""
    # Verify device exists
    result = await db.execute(select(Device).where(Device.id == log_data.device_id))
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    # Create maintenance log
    maintenance_log = MaintenanceLog(
        id=str(uuid.uuid4()),
        device_id=log_data.device_id,
        maintenance_type=log_data.maintenance_type,
        description=log_data.description,
        scheduled_at=log_data.scheduled_at,
        notes=log_data.notes,
        parts_replaced=log_data.parts_replaced,
        cost=log_data.cost,
        technician_id=current_user.id,
        created_by=current_user.id
    )

    db.add(maintenance_log)
    await db.commit()
    await db.refresh(maintenance_log)

    return MaintenanceLogResponse.from_orm(maintenance_log)


@router.get("/fleet/maintenance", response_model=List[MaintenanceLogResponse])
async def list_maintenance_logs(
    device_id: str = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List maintenance logs"""
    query = select(MaintenanceLog).order_by(MaintenanceLog.created_at.desc())

    if device_id:
        query = query.where(MaintenanceLog.device_id == device_id)

    result = await db.execute(query)
    logs = result.scalars().all()

    return [MaintenanceLogResponse.from_orm(log) for log in logs]


@router.put("/fleet/maintenance/{log_id}/complete")
async def complete_maintenance(
    log_id: str,
    notes: str = "",
    current_user: User = Depends(RoleChecker([UserRole.ADMIN, UserRole.ENGINEER])),
    db: AsyncSession = Depends(get_db)
):
    """Mark maintenance as completed"""
    result = await db.execute(select(MaintenanceLog).where(MaintenanceLog.id == log_id))
    log = result.scalar_one_or_none()

    if not log:
        raise HTTPException(status_code=404, detail="Maintenance log not found")

    log.status = "completed"
    log.completed_at = datetime.utcnow()
    if notes:
        log.notes = f"{log.notes}\n\nCompletion notes: {notes}"

    await db.commit()

    return {"message": "Maintenance marked as completed"}
