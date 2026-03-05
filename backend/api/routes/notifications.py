"""API routes for notification management."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.models.alert import Alert
from backend.services.notifications.notification_manager import (
    NotificationChannel,
    NotificationManager,
)

router = APIRouter(prefix="/notifications", tags=["notifications"])


class TestNotificationInput(BaseModel):
    channels: list[str] = ["email"]
    message: str = "Test notification from FMCG Intelligence Platform"


@router.post("/test")
async def send_test_notification(
    data: TestNotificationInput, db: AsyncSession = Depends(get_db)
):
    """Send a test notification to verify channel configuration."""
    manager = _get_notification_manager(db)

    results = {}
    for channel_name in data.channels:
        handler = manager._channels.get(channel_name)
        if not handler:
            results[channel_name] = {"status": "not_configured"}
            continue
        try:
            result = await handler.send(
                title="Test Notification",
                message=data.message,
                severity="info",
                priority="low",
            )
            results[channel_name] = result
        except Exception as e:
            results[channel_name] = {"status": "error", "error": str(e)}

    return {"results": results}


@router.post("/send-alert/{alert_id}")
async def send_alert_notification(
    alert_id: int, db: AsyncSession = Depends(get_db)
):
    """Manually trigger notification for a specific alert."""
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        return {"error": "Alert not found"}

    manager = _get_notification_manager(db)
    return await manager.notify(alert)


@router.post("/daily-digest")
async def send_daily_digest(
    channels: list[str] | None = None, db: AsyncSession = Depends(get_db)
):
    """Manually trigger the daily digest email/notification."""
    from backend.services.ai_engine.intelligence_engine import IntelligenceEngine
    from backend.services.erp_integration.erp_client import ERPClient
    from backend.services.market_data.commodity_tracker import CommodityTracker
    from backend.services.pos_integration.pos_client import POSClient
    from backend.services.supply_chain.risk_analyzer import SupplyChainRiskAnalyzer

    # Generate briefing content
    tracker = CommodityTracker(db)
    risk_analyzer = SupplyChainRiskAnalyzer(db)
    erp = ERPClient(db)
    pos = POSClient(db)
    engine = IntelligenceEngine(db)

    commodity_prices = await tracker.get_latest_prices()
    supply_chain = await risk_analyzer.get_supply_chain_overview()
    low_stock = await erp.get_low_stock_products()
    top_selling = await pos.get_top_selling_products()

    alert_result = await db.execute(
        select(Alert)
        .where(Alert.is_resolved.is_(False))
        .order_by(Alert.created_at.desc())
        .limit(10)
    )
    alerts = alert_result.scalars().all()
    recent_alerts = [
        {"type": a.alert_type.value, "severity": a.severity.value, "title": a.title}
        for a in alerts
    ]

    insight = await engine.generate_daily_briefing(
        commodity_prices, supply_chain, low_stock, top_selling, recent_alerts
    )

    briefing_content = {
        "title": insight.title,
        "summary": insight.summary,
        "detailed_analysis": insight.detailed_analysis,
        "recommended_actions": insight.recommended_actions,
    }

    # Send through notification channels
    manager = _get_notification_manager(db)
    result = await manager.send_daily_digest(briefing_content, channels)

    return {"insight_id": insight.id, "notification_results": result}


@router.get("/channels")
async def get_configured_channels():
    """List configured notification channels and their status."""
    from backend.core.config import settings

    channels = {
        "email": {
            "configured": bool(settings.smtp_host),
            "recipients": len(settings.email_recipients),
        },
        "whatsapp": {
            "configured": bool(settings.whatsapp_api_token),
            "recipients": len(settings.whatsapp_recipients),
        },
        "slack": {
            "configured": bool(settings.slack_webhook_url),
            "channel": settings.slack_channel,
        },
        "telegram": {
            "configured": bool(settings.telegram_bot_token),
            "chat_id": bool(settings.telegram_chat_id),
        },
    }
    return {"channels": channels}


def _get_notification_manager(db: AsyncSession) -> NotificationManager:
    """Initialize notification manager with all configured channels."""
    from backend.core.config import settings

    manager = NotificationManager(db)

    if settings.smtp_host:
        from backend.services.notifications.email import EmailNotifier

        manager.register_channel(NotificationChannel.EMAIL, EmailNotifier())

    if settings.whatsapp_api_token:
        from backend.services.notifications.whatsapp import WhatsAppNotifier

        manager.register_channel(NotificationChannel.WHATSAPP, WhatsAppNotifier())

    if settings.slack_webhook_url:
        from backend.services.notifications.slack_telegram import SlackNotifier

        manager.register_channel(NotificationChannel.SLACK, SlackNotifier())

    if settings.telegram_bot_token:
        from backend.services.notifications.slack_telegram import TelegramNotifier

        manager.register_channel(NotificationChannel.TELEGRAM, TelegramNotifier())

    return manager
