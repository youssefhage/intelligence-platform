"""Unified notification manager for multi-channel alert delivery."""

import json
from datetime import datetime
from enum import Enum

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import settings
from backend.models.alert import Alert, AlertSeverity

logger = structlog.get_logger()


class NotificationChannel(str, Enum):
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    SLACK = "slack"
    TELEGRAM = "telegram"


class NotificationPriority(str, Enum):
    LOW = "low"       # Informational — batch in daily digest
    MEDIUM = "medium"  # Important — send within 1 hour
    HIGH = "high"      # Urgent — send immediately


class NotificationManager:
    """Routes notifications to appropriate channels based on severity and preference."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._channels: dict[str, object] = {}
        self._routing_rules: list[dict] = []

    def register_channel(self, channel_type: NotificationChannel, handler):
        """Register a notification channel handler."""
        self._channels[channel_type.value] = handler

    def add_routing_rule(
        self,
        alert_severity: AlertSeverity | None = None,
        alert_type: str | None = None,
        channels: list[NotificationChannel] | None = None,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
    ):
        """Add a rule for routing alerts to specific channels."""
        self._routing_rules.append(
            {
                "severity": alert_severity,
                "alert_type": alert_type,
                "channels": [c.value for c in (channels or [])],
                "priority": priority,
            }
        )

    async def notify(self, alert: Alert) -> dict:
        """Send notification for an alert through appropriate channels."""
        channels = self._determine_channels(alert)
        priority = self._determine_priority(alert)

        results = {}
        for channel_name in channels:
            handler = self._channels.get(channel_name)
            if not handler:
                results[channel_name] = {"status": "skipped", "reason": "not configured"}
                continue

            try:
                result = await handler.send(
                    title=alert.title,
                    message=alert.message,
                    severity=alert.severity.value,
                    action_recommended=alert.action_recommended,
                    priority=priority.value,
                )
                results[channel_name] = {"status": "sent", **result}
            except Exception as e:
                logger.error(
                    "Notification send failed",
                    channel=channel_name,
                    error=str(e),
                )
                results[channel_name] = {"status": "error", "error": str(e)}

        return {
            "alert_id": alert.id,
            "channels_attempted": len(channels),
            "results": results,
            "sent_at": datetime.utcnow().isoformat(),
        }

    async def send_daily_digest(
        self, briefing_content: dict, channels: list[str] | None = None
    ) -> dict:
        """Send the daily intelligence briefing digest."""
        target_channels = channels or list(self._channels.keys())

        results = {}
        for channel_name in target_channels:
            handler = self._channels.get(channel_name)
            if not handler:
                continue

            try:
                result = await handler.send_digest(briefing_content)
                results[channel_name] = {"status": "sent", **result}
            except Exception as e:
                logger.error(
                    "Digest send failed",
                    channel=channel_name,
                    error=str(e),
                )
                results[channel_name] = {"status": "error", "error": str(e)}

        return results

    def _determine_channels(self, alert: Alert) -> list[str]:
        """Determine which channels to use based on routing rules."""
        matched_channels = set()

        for rule in self._routing_rules:
            if rule["severity"] and rule["severity"] != alert.severity:
                continue
            if rule["alert_type"] and rule["alert_type"] != alert.alert_type.value:
                continue
            matched_channels.update(rule["channels"])

        # Default routing if no rules match
        if not matched_channels:
            if alert.severity == AlertSeverity.CRITICAL:
                matched_channels = set(self._channels.keys())
            elif alert.severity == AlertSeverity.WARNING:
                matched_channels = {"email", "slack"}
            else:
                matched_channels = {"email"}

        return [c for c in matched_channels if c in self._channels]

    def _determine_priority(self, alert: Alert) -> NotificationPriority:
        if alert.severity == AlertSeverity.CRITICAL:
            return NotificationPriority.HIGH
        if alert.severity == AlertSeverity.WARNING:
            return NotificationPriority.MEDIUM
        return NotificationPriority.LOW
