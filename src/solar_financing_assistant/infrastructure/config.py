"""Application settings loaded from environment variables / .env file."""

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
