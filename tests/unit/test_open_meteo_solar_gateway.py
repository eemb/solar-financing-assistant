"""Unit tests for OpenMeteoSolarGateway using monkeypatched requests.get."""

import pytest

from solar_financing_assistant.infrastructure.gateways.open_meteo_solar_gateway import (
    OpenMeteoSolarGateway,
)

FAKE_RESPONSE_DATA = {
    "hourly": {
        "shortwave_radiation": [0, 0, 100, 300, 600, 800, 700, 400, 100, 0],
    }
}


class _FakeResponse:
    def raise_for_status(self) -> None:
        pass

    def json(self) -> dict:
        return FAKE_RESPONSE_DATA


def test_returns_correct_latitude_and_longitude(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "solar_financing_assistant.infrastructure.gateways.open_meteo_solar_gateway.requests.get",
        lambda *args, **kwargs: _FakeResponse(),
    )

    gateway = OpenMeteoSolarGateway()
    result = gateway.get_solar_potential(latitude=-8.0476, longitude=-34.877)

    assert result.latitude == -8.0476
    assert result.longitude == -34.877


def test_average_shortwave_radiation_is_positive(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "solar_financing_assistant.infrastructure.gateways.open_meteo_solar_gateway.requests.get",
        lambda *args, **kwargs: _FakeResponse(),
    )

    gateway = OpenMeteoSolarGateway()
    result = gateway.get_solar_potential(latitude=-8.0476, longitude=-34.877)

    assert result.average_shortwave_radiation is not None
    assert result.average_shortwave_radiation > 0


def test_estimated_daily_generation_is_positive(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "solar_financing_assistant.infrastructure.gateways.open_meteo_solar_gateway.requests.get",
        lambda *args, **kwargs: _FakeResponse(),
    )

    gateway = OpenMeteoSolarGateway()
    result = gateway.get_solar_potential(latitude=-8.0476, longitude=-34.877)

    assert result.estimated_daily_generation_kwh_per_kwp > 0
