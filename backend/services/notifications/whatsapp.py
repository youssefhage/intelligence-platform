"""WhatsApp Business API integration for alert notifications."""

import json
from datetime import datetime

import httpx
import structlog

from backend.core.config import settings

logger = structlog.get_logger()


class WhatsAppNotifier:
    """Sends notifications via WhatsApp Business API.

    Uses the Meta Cloud API for WhatsApp Business. Requires:
    - A WhatsApp Business Account
    - A registered phone number
    - An API access token
    """

    def __init__(self):
        self.api_url = (
            f"https://graph.facebook.com/v18.0/"
            f"{settings.whatsapp_phone_number_id}/messages"
        )
        self.client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {settings.whatsapp_api_token}",
                "Content-Type": "application/json",
            },
            timeout=15.0,
        )

    async def send(
        self,
        title: str,
        message: str,
        severity: str,
        action_recommended: str | None = None,
        priority: str = "medium",
    ) -> dict:
        """Send an alert notification via WhatsApp."""
        severity_emoji = {
            "critical": "\u26a0\ufe0f",
            "warning": "\u26a0",
            "info": "\u2139\ufe0f",
        }
        emoji = severity_emoji.get(severity, "\u2139\ufe0f")

        text = f"{emoji} *{title}*\n\n{message}"
        if action_recommended:
            text += f"\n\n*Recommended Action:*\n{action_recommended}"
        text += f"\n\n_{datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}_"

        for recipient in settings.whatsapp_recipients:
            payload = {
                "messaging_product": "whatsapp",
                "to": recipient,
                "type": "text",
                "text": {"preview_url": False, "body": text},
            }

            try:
                response = await self.client.post(self.api_url, json=payload)
                response.raise_for_status()
                logger.info("WhatsApp message sent", recipient=recipient)
            except Exception as e:
                logger.error(
                    "WhatsApp send failed",
                    recipient=recipient,
                    error=str(e),
                )

        return {"recipients": len(settings.whatsapp_recipients)}

    async def send_digest(self, briefing_content: dict) -> dict:
        """Send daily digest via WhatsApp."""
        title = briefing_content.get("title", "Daily Intelligence Briefing")
        summary = briefing_content.get("summary", "")

        actions = briefing_content.get("recommended_actions", "[]")
        if isinstance(actions, str):
            try:
                actions = json.loads(actions)
            except json.JSONDecodeError:
                actions = [actions]

        text = f"*{title}*\n\n{summary}"
        if actions:
            text += "\n\n*Key Actions:*"
            for i, action in enumerate(actions[:5], 1):
                text += f"\n{i}. {action}"

        text += f"\n\n_{datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}_"

        for recipient in settings.whatsapp_recipients:
            payload = {
                "messaging_product": "whatsapp",
                "to": recipient,
                "type": "text",
                "text": {"preview_url": False, "body": text},
            }
            try:
                response = await self.client.post(self.api_url, json=payload)
                response.raise_for_status()
            except Exception as e:
                logger.error("WhatsApp digest failed", error=str(e))

        return {"recipients": len(settings.whatsapp_recipients)}

    async def close(self):
        await self.client.aclose()
