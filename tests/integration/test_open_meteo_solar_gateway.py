"""Integration tests for OpenMeteoSolarGateway (requires network access)."""

import pytest

from solar_financing_assistant.infrastructure.gateways.open_meteo_solar_gateway import (
    OpenMeteoSolarGateway,
)

RECIFE_LATITUDE = -8.0476
RECIFE_LONGITUDE = -34.877


@pytest.mark.integration
def test_returns_correct_coordinates() -> None:
    gateway = OpenMeteoSolarGateway()
    result = gateway.get_solar_potential(
        latitude=RECIFE_LATITUDE, longitude=RECIFE_LONGITUDE
    )

    assert result.latitude == RECIFE_LATITUDE
    assert result.longitude == RECIFE_LONGITUDE


@pytest.mark.integration
def test_estimated_daily_generation_is_positive() -> None:
    gateway = OpenMeteoSolarGateway()
    result = gateway.get_solar_potential(
        latitude=RECIFE_LATITUDE, longitude=RECIFE_LONGITUDE
    )

    assert result.estimated_daily_generation_kwh_per_kwp > 0
