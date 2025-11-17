import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import uuid

from ..models.alert import Alert, AlertRule, AlertSeverity, AlertStatus, AlertType
from ..models.device import Device
from ..core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class AlertService:
    """Service for managing alerts and alert rules"""

    async def evaluate_rules_for_device(
        self,
        device_id: str,
        device_type: str,
        data: Dict[str, Any]
    ):
        """Evaluate all applicable alert rules for a device's data"""
        async with AsyncSessionLocal() as db:
            try:
                # Get all enabled rules for this device type
                result = await db.execute(
                    select(AlertRule).where(
                        and_(
                            AlertRule.is_enabled == True,
                            (AlertRule.device_type == device_type) | (AlertRule.device_type == None)
                        )
                    )
                )
                rules = result.scalars().all()

                # Get device info
                device_result = await db.execute(
                    select(Device).where(Device.id == device_id)
                )
                device = device_result.scalar_one_or_none()

                if not device:
                    logger.warning(f"Device {device_id} not found")
                    return

                # Evaluate each rule
                for rule in rules:
                    try:
                        if await self._evaluate_rule(rule, device, data, db):
                            # Rule triggered - create alert
                            await self._create_alert_from_rule(rule, device, data, db)
                    except Exception as e:
                        logger.error(f"Error evaluating rule {rule.id}: {e}")

                await db.commit()

            except Exception as e:
                logger.error(f"Error evaluating rules for device {device_id}: {e}")
                await db.rollback()

    async def _evaluate_rule(
        self,
        rule: AlertRule,
        device: Device,
        data: Dict[str, Any],
        db: AsyncSession
    ) -> bool:
        """Evaluate if a rule should trigger"""
        try:
            # Check if metric exists in data
            metric_value = data.get(rule.metric_name)
            if metric_value is None:
                return False

            # Check geofencing if enabled
            if rule.geo_fence_enabled:
                if not self._is_within_geofence(
                    device.latitude,
                    device.longitude,
                    rule.geo_fence_center_lat,
                    rule.geo_fence_center_lon,
                    rule.geo_fence_radius_meters
                ):
                    return False

            # Evaluate condition
            triggered = False
            if rule.condition == "gt":
                triggered = float(metric_value) > rule.threshold_value
            elif rule.condition == "gte":
                triggered = float(metric_value) >= rule.threshold_value
            elif rule.condition == "lt":
                triggered = float(metric_value) < rule.threshold_value
            elif rule.condition == "lte":
                triggered = float(metric_value) <= rule.threshold_value
            elif rule.condition == "eq":
                triggered = float(metric_value) == rule.threshold_value
            elif rule.condition == "between":
                triggered = rule.threshold_min <= float(metric_value) <= rule.threshold_max

            if not triggered:
                return False

            # Check suppression
            if rule.suppression_enabled:
                suppression_window = datetime.utcnow() - timedelta(minutes=rule.suppression_minutes)
                recent_alert = await db.execute(
                    select(Alert).where(
                        and_(
                            Alert.rule_id == rule.id,
                            Alert.device_id == device.id,
                            Alert.triggered_at > suppression_window
                        )
                    ).limit(1)
                )
                if recent_alert.scalar_one_or_none():
                    logger.debug(f"Alert suppressed for rule {rule.id} on device {device.id}")
                    return False

            return True

        except Exception as e:
            logger.error(f"Error evaluating rule condition: {e}")
            return False

    def _is_within_geofence(
        self,
        device_lat: float,
        device_lon: float,
        fence_lat: float,
        fence_lon: float,
        radius_meters: float
    ) -> bool:
        """Check if device is within geofence"""
        from math import radians, sin, cos, sqrt, atan2

        # Haversine formula
        R = 6371000  # Earth radius in meters

        lat1 = radians(device_lat)
        lon1 = radians(device_lon)
        lat2 = radians(fence_lat)
        lon2 = radians(fence_lon)

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        distance = R * c

        return distance <= radius_meters

    async def _create_alert_from_rule(
        self,
        rule: AlertRule,
        device: Device,
        data: Dict[str, Any],
        db: AsyncSession
    ):
        """Create an alert from a triggered rule"""
        try:
            metric_value = data.get(rule.metric_name)

            alert = Alert(
                id=str(uuid.uuid4()),
                device_id=device.id,
                rule_id=rule.id,
                alert_type=rule.alert_type,
                severity=rule.severity,
                status=AlertStatus.OPEN,
                title=f"{rule.name} - {device.name}",
                description=rule.description,
                value=float(metric_value) if metric_value else None,
                threshold=rule.threshold_value,
                unit=data.get('unit'),
                latitude=device.latitude,
                longitude=device.longitude,
                notification_channels=rule.notification_channels,
                metadata={
                    'device_name': device.name,
                    'device_type': device.device_type,
                    'zone': device.zone,
                    'data': data
                }
            )

            db.add(alert)
            await db.flush()

            logger.warning(
                f"Alert created: {alert.title} - {rule.metric_name}={metric_value} "
                f"(threshold: {rule.threshold_value})"
            )

            # Send notifications (async)
            await self._send_alert_notifications(alert, rule, db)

        except Exception as e:
            logger.error(f"Error creating alert from rule: {e}")

    async def _send_alert_notifications(
        self,
        alert: Alert,
        rule: AlertRule,
        db: AsyncSession
    ):
        """Send alert notifications through configured channels"""
        try:
            notifications_sent = []

            for channel in rule.notification_channels:
                if channel == "email":
                    # Send email notification
                    for recipient in rule.notification_recipients:
                        # Email sending logic would go here
                        logger.info(f"Would send email alert to {recipient}")
                        notifications_sent.append({
                            'channel': 'email',
                            'recipient': recipient,
                            'sent_at': datetime.utcnow().isoformat()
                        })

                elif channel == "webhook":
                    # Send webhook notification
                    logger.info(f"Would send webhook notification")
                    notifications_sent.append({
                        'channel': 'webhook',
                        'sent_at': datetime.utcnow().isoformat()
                    })

            alert.notifications_sent = notifications_sent
            await db.flush()

        except Exception as e:
            logger.error(f"Error sending alert notifications: {e}")

    async def acknowledge_alert(self, alert_id: str, user_id: str, notes: Optional[str] = None):
        """Acknowledge an alert"""
        async with AsyncSessionLocal() as db:
            try:
                result = await db.execute(select(Alert).where(Alert.id == alert_id))
                alert = result.scalar_one_or_none()

                if not alert:
                    raise ValueError(f"Alert {alert_id} not found")

                alert.status = AlertStatus.ACKNOWLEDGED
                alert.acknowledged_at = datetime.utcnow()
                alert.acknowledged_by = user_id
                if notes:
                    alert.resolution_notes = notes

                await db.commit()
                logger.info(f"Alert {alert_id} acknowledged by {user_id}")

            except Exception as e:
                await db.rollback()
                logger.error(f"Error acknowledging alert: {e}")
                raise

    async def resolve_alert(self, alert_id: str, user_id: str, resolution_notes: str):
        """Resolve an alert"""
        async with AsyncSessionLocal() as db:
            try:
                result = await db.execute(select(Alert).where(Alert.id == alert_id))
                alert = result.scalar_one_or_none()

                if not alert:
                    raise ValueError(f"Alert {alert_id} not found")

                alert.status = AlertStatus.RESOLVED
                alert.resolved_at = datetime.utcnow()
                alert.resolved_by = user_id
                alert.resolution_notes = resolution_notes

                await db.commit()
                logger.info(f"Alert {alert_id} resolved by {user_id}")

            except Exception as e:
                await db.rollback()
                logger.error(f"Error resolving alert: {e}")
                raise


# Global instance
alert_service = AlertService()
