"""Shared AI client using Moonshot Kimi (OpenAI-compatible API)."""

from openai import AsyncOpenAI, OpenAI

from backend.core.config import settings


def get_sync_client() -> OpenAI:
    """Get a synchronous OpenAI-compatible client for Kimi."""
    return OpenAI(
        api_key=settings.ai_api_key,
        base_url=settings.ai_base_url,
    )


def get_async_client() -> AsyncOpenAI:
    """Get an async OpenAI-compatible client for Kimi."""
    return AsyncOpenAI(
        api_key=settings.ai_api_key,
        base_url=settings.ai_base_url,
    )


def is_configured() -> bool:
    """Check if AI API key is configured."""
    return bool(settings.ai_api_key)


MODEL = settings.ai_model if settings.ai_api_key else "kimi-latest"
