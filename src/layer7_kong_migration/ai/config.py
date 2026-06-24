"""AI configuration loader."""

from typing import Any


def get_ai_config() -> dict[str, Any]:
    try:
        from dynaconf import Dynaconf

        settings = Dynaconf(settings_files=["config/settings.toml", "config/.secrets.toml"])
        return {
            "model": settings.get("ai_model", "claude-sonnet-4-20250514"),
            "max_tokens": settings.get("ai_max_tokens", 2000),
            "max_resource_chars": settings.get("ai_max_resource_chars", 4000),
            "rate_limit_delay_ms": settings.get("ai_rate_limit_delay_ms", 500),
            "max_retries": settings.get("ai_max_retries", 3),
            "confidence_auto_threshold": settings.get("ai_confidence_auto_threshold", 0.85),
            "confidence_review_threshold": settings.get("ai_confidence_review_threshold", 0.60),
        }
    except Exception:
        return {
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 2000,
            "max_resource_chars": 4000,
            "rate_limit_delay_ms": 500,
            "max_retries": 3,
            "confidence_auto_threshold": 0.85,
            "confidence_review_threshold": 0.60,
        }
