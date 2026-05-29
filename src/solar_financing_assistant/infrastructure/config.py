"""Application settings loaded from environment variables / .env file."""

import logging
import logging.config
from decimal import Decimal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    log_level: str = "INFO"

    monthly_rate: Decimal = Field(
        default=Decimal("0.019"),
        description="Monthly interest rate applied to all financing simulations.",
    )
    http_timeout_seconds: float = Field(
        default=10.0,
        description="Default timeout (seconds) for all outbound HTTP calls.",
    )


settings = Settings()


def configure_logging() -> None:
    """Configure root logger using the log_level from settings.

    Call once at application startup (e.g. in ``__main__.py``).
    """
    logging.basicConfig(
        level=settings.log_level.upper(),
        format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
