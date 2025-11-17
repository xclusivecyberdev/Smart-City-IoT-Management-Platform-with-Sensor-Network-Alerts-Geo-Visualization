from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from typing import Optional
import uuid

from ..core.database import get_db
from ..core.security import get_current_user, RoleChecker
from ..models.alert import Alert, AlertRule, AlertSeverity, AlertStatus, AlertType
from ..models.user import User, UserRole
from ..schemas.alert import (
    AlertRuleCreate, AlertRuleUpdate, AlertRuleResponse,
    AlertResponse, AlertListResponse, AlertAcknowledge, AlertResolve
)
from ..services.alert_service import alert_service

router = APIRouter()


# Alert Rules
@router.post("/alert-rules", response_model=AlertRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_alert_rule(
    rule_data: AlertRuleCreate,
    current_user: User = Depends(RoleChecker([UserRole.ADMIN, UserRole.ENGINEER])),
    db: AsyncSession = Depends(get_db)
):
    """Create a new alert rule"""
    rule = AlertRule(
        id=str(uuid.uuid4()),
        name=rule_data.name,
        description=rule_data.description,
        device_type=rule_data.device_type,
        metric_name=rule_data.metric_name,
        condition=rule_data.condition,
        threshold_value=rule_data.threshold_value,
        threshold_min=rule_data.threshold_min,
        threshold_max=rule_data.threshold_max,
        severity=rule_data.severity,
        alert_type=rule_data.alert_type,
        time_window_minutes=rule_data.time_window_minutes,
        evaluation_interval_seconds=rule_data.evaluation_interval_seconds,
        notification_channels=rule_data.notification_channels,
        notification_recipients=rule_data.notification_recipients,
        suppression_enabled=rule_data.suppression_enabled,
        suppression_minutes=rule_data.suppression_minutes,
        is_enabled=rule_data.is_enabled,
        geo_fence_enabled=rule_data.geo_fence_enabled,
        geo_fence_center_lat=rule_data.geo_fence_center_lat,
        geo_fence_center_lon=rule_data.geo_fence_center_lon,
        geo_fence_radius_meters=rule_data.geo_fence_radius_meters,
        conditions=rule_data.conditions,
        created_by=current_user.id
    )

    db.add(rule)
    await db.commit()
    await db.refresh(rule)

    return AlertRuleResponse.from_orm(rule)


@router.get("/alert-rules", response_model=list[AlertRuleResponse])
async def list_alert_rules(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all alert rules"""
    result = await db.execute(select(AlertRule))
    rules = result.scalars().all()

    return [AlertRuleResponse.from_orm(rule) for rule in rules]


@router.get("/alert-rules/{rule_id}", response_model=AlertRuleResponse)
async def get_alert_rule(
    rule_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get alert rule by ID"""
    result = await db.execute(select(AlertRule).where(AlertRule.id == rule_id))
    rule = result.scalar_one_or_none()

    if not rule:
        raise HTTPException(status_code=404, detail="Alert rule not found")

    return AlertRuleResponse.from_orm(rule)


@router.put("/alert-rules/{rule_id}", response_model=AlertRuleResponse)
async def update_alert_rule(
    rule_id: str,
    rule_data: AlertRuleUpdate,
    current_user: User = Depends(RoleChecker([UserRole.ADMIN, UserRole.ENGINEER])),
    db: AsyncSession = Depends(get_db)
):
    """Update alert rule"""
    result = await db.execute(select(AlertRule).where(AlertRule.id == rule_id))
    rule = result.scalar_one_or_none()

    if not rule:
        raise HTTPException(status_code=404, detail="Alert rule not found")

    update_data = rule_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(rule, field, value)

    await db.commit()
    await db.refresh(rule)

    return AlertRuleResponse.from_orm(rule)


@router.delete("/alert-rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert_rule(
    rule_id: str,
    current_user: User = Depends(RoleChecker([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """Delete alert rule"""
    result = await db.execute(select(AlertRule).where(AlertRule.id == rule_id))
    rule = result.scalar_one_or_none()

    if not rule:
        raise HTTPException(status_code=404, detail="Alert rule not found")

    await db.delete(rule)
    await db.commit()


# Alerts
@router.get("/alerts", response_model=AlertListResponse)
async def list_alerts(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    status: Optional[AlertStatus] = None,
    severity: Optional[AlertSeverity] = None,
    alert_type: Optional[AlertType] = None,
    device_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List alerts with filtering and pagination"""
    query = select(Alert).order_by(Alert.triggered_at.desc())

    # Apply filters
    filters = []
    if status:
        filters.append(Alert.status == status)
    if severity:
        filters.append(Alert.severity == severity)
    if alert_type:
        filters.append(Alert.alert_type == alert_type)
    if device_id:
        filters.append(Alert.device_id == device_id)

    if filters:
        query = query.where(and_(*filters))

    # Get total count
    count_query = select(func.count()).select_from(Alert)
    if filters:
        count_query = count_query.where(and_(*filters))
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    # Execute query
    result = await db.execute(query)
    alerts = result.scalars().all()

    return AlertListResponse(
        alerts=[AlertResponse.from_orm(a) for a in alerts],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/alerts/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get alert by ID"""
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    return AlertResponse.from_orm(alert)


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    ack_data: AlertAcknowledge,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Acknowledge an alert"""
    try:
        await alert_service.acknowledge_alert(
            alert_id=alert_id,
            user_id=current_user.id,
            notes=ack_data.notes
        )
        return {"message": "Alert acknowledged successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    resolve_data: AlertResolve,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Resolve an alert"""
    try:
        await alert_service.resolve_alert(
            alert_id=alert_id,
            user_id=current_user.id,
            resolution_notes=resolve_data.resolution_notes
        )
        return {"message": "Alert resolved successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts/statistics/summary")
async def get_alerts_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get alerts summary statistics"""
    # Count by status
    status_counts = {}
    for alert_status in AlertStatus:
        result = await db.execute(
            select(func.count()).select_from(Alert).where(Alert.status == alert_status)
        )
        status_counts[alert_status.value] = result.scalar()

    # Count by severity
    severity_counts = {}
    for severity in AlertSeverity:
        result = await db.execute(
            select(func.count()).select_from(Alert).where(Alert.severity == severity)
        )
        severity_counts[severity.value] = result.scalar()

    return {
        "status_counts": status_counts,
        "severity_counts": severity_counts
    }
