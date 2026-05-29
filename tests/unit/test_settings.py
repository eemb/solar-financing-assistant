"""Unit tests for application Settings."""

from decimal import Decimal

from solar_financing_assistant.config.settings import Settings


def test_settings_has_monthly_rate() -> None:
    s = Settings()
    assert isinstance(s.monthly_rate, Decimal)
    assert s.monthly_rate > 0


def test_settings_has_generation_per_kwp_month() -> None:
    s = Settings()
    assert isinstance(s.generation_per_kwp_month, float)
    assert s.generation_per_kwp_month > 0


def test_settings_has_cost_per_kwp_brl() -> None:
    s = Settings()
    assert isinstance(s.cost_per_kwp_brl, Decimal)
    assert s.cost_per_kwp_brl > 0


def test_settings_has_http_timeout_seconds() -> None:
    s = Settings()
    assert isinstance(s.http_timeout_seconds, float)
    assert s.http_timeout_seconds > 0


def test_settings_defaults() -> None:
    s = Settings()
    assert s.monthly_rate == Decimal("0.019")
    assert s.generation_per_kwp_month == 120.0
    assert s.cost_per_kwp_brl == Decimal("5000.00")
    assert s.http_timeout_seconds == 10.0
