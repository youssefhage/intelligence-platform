"""Slack and Telegram notification integrations."""

import json
from datetime import datetime

import httpx
import structlog

from backend.core.config import settings

logger = structlog.get_logger()


class SlackNotifier:
    """Sends notifications via Slack Incoming Webhooks."""

    def __init__(self):
        self.webhook_url = settings.slack_webhook_url
        self.channel = settings.slack_channel
        self.client = httpx.AsyncClient(timeout=10.0)

    async def send(
        self,
        title: str,
        message: str,
        severity: str,
        action_recommended: str | None = None,
        priority: str = "medium",
    ) -> dict:
        """Send an alert to Slack."""
        if not self.webhook_url:
            return {"status": "skipped", "reason": "Slack not configured"}

        color_map = {"critical": "#dc2626", "warning": "#f59e0b", "info": "#3b82f6"}
        emoji_map = {"critical": ":rotating_light:", "warning": ":warning:", "info": ":information_source:"}

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji_map.get(severity, ':bell:')} {title}",
                },
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": message},
            },
        ]

        if action_recommended:
            blocks.append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Recommended Action:*\n{action_recommended}",
                    },
                }
            )

        blocks.append(
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": (
                            f"FMCG Intelligence Platform | "
                            f"{severity.upper()} | "
                            f"{datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}"
                        ),
                    }
                ],
            }
        )

        payload = {
            "channel": self.channel,
            "attachments": [
                {
                    "color": color_map.get(severity, "#3b82f6"),
                    "blocks": blocks,
                }
            ],
        }

        try:
            response = await self.client.post(self.webhook_url, json=payload)
            response.raise_for_status()
            return {"status": "sent"}
        except Exception as e:
            logger.error("Slack send failed", error=str(e))
            return {"status": "error", "error": str(e)}

    async def send_digest(self, briefing_content: dict) -> dict:
        """Send daily digest to Slack."""
        if not self.webhook_url:
            return {"status": "skipped", "reason": "Slack not configured"}

        title = briefing_content.get("title", "Daily Briefing")
        summary = briefing_content.get("summary", "")
        actions = briefing_content.get("recommended_actions", "[]")
        if isinstance(actions, str):
            try:
                actions = json.loads(actions)
            except json.JSONDecodeError:
                actions = []

        actions_text = "\n".join(f"{i}. {a}" for i, a in enumerate(actions[:5], 1))

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f":chart_with_upwards_trend: {title}",
                },
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Summary*\n{summary}"},
            },
        ]

        if actions_text:
            blocks.append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Key Actions*\n{actions_text}",
                    },
                }
            )

        payload = {
            "channel": self.channel,
            "attachments": [{"color": "#0f172a", "blocks": blocks}],
        }

        try:
            response = await self.client.post(self.webhook_url, json=payload)
            response.raise_for_status()
            return {"status": "sent"}
        except Exception as e:
            logger.error("Slack digest failed", error=str(e))
            return {"status": "error", "error": str(e)}

    async def close(self):
        await self.client.aclose()


class TelegramNotifier:
    """Sends notifications via Telegram Bot API."""

    def __init__(self):
        self.bot_token = settings.telegram_bot_token
        self.chat_id = settings.telegram_chat_id
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.client = httpx.AsyncClient(timeout=10.0)

    async def send(
        self,
        title: str,
        message: str,
        severity: str,
        action_recommended: str | None = None,
        priority: str = "medium",
    ) -> dict:
        """Send an alert via Telegram."""
        if not self.bot_token or not self.chat_id:
            return {"status": "skipped", "reason": "Telegram not configured"}

        severity_emoji = {
            "critical": "\u26a0\ufe0f",
            "warning": "\u26a0",
            "info": "\u2139\ufe0f",
        }
        emoji = severity_emoji.get(severity, "\u2139\ufe0f")

        text = f"{emoji} <b>{title}</b>\n\n{message}"
        if action_recommended:
            text += f"\n\n<b>Recommended Action:</b>\n{action_recommended}"
        text += f"\n\n<i>{datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}</i>"

        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "HTML",
        }

        try:
            response = await self.client.post(
                f"{self.base_url}/sendMessage", json=payload
            )
            response.raise_for_status()
            return {"status": "sent"}
        except Exception as e:
            logger.error("Telegram send failed", error=str(e))
            return {"status": "error", "error": str(e)}

    async def send_digest(self, briefing_content: dict) -> dict:
        """Send daily digest via Telegram."""
        if not self.bot_token or not self.chat_id:
            return {"status": "skipped", "reason": "Telegram not configured"}

        title = briefing_content.get("title", "Daily Briefing")
        summary = briefing_content.get("summary", "")

        actions = briefing_content.get("recommended_actions", "[]")
        if isinstance(actions, str):
            try:
                actions = json.loads(actions)
            except json.JSONDecodeError:
                actions = []

        text = f"\U0001f4ca <b>{title}</b>\n\n{summary}"
        if actions:
            text += "\n\n<b>Key Actions:</b>"
            for i, action in enumerate(actions[:5], 1):
                text += f"\n{i}. {action}"

        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "HTML",
        }

        try:
            response = await self.client.post(
                f"{self.base_url}/sendMessage", json=payload
            )
            response.raise_for_status()
            return {"status": "sent"}
        except Exception as e:
            logger.error("Telegram digest failed", error=str(e))
            return {"status": "error", "error": str(e)}

    async def close(self):
        await self.client.aclose()
