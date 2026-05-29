"""Unit tests for OpenMeteoSolarGateway using a mocked httpx.AsyncClient."""

from unittest.mock import AsyncMock, MagicMock, patch

from solar_financing_assistant.infrastructure.gateways.open_meteo_solar_gateway import (
    OpenMeteoSolarGateway,
)

FAKE_RESPONSE_DATA = {
    "hourly": {
        "shortwave_radiation": [0, 0, 100, 300, 600, 800, 700, 400, 100, 0],
    }
}


def _make_mock_client() -> AsyncMock:
    """Return an AsyncMock that behaves like an async context manager httpx client."""
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = FAKE_RESPONSE_DATA

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.get = AsyncMock(return_value=mock_response)
    return mock_client


async def test_returns_correct_latitude_and_longitude() -> None:
    with patch(
        "solar_financing_assistant.infrastructure.gateways.open_meteo_solar_gateway.httpx.AsyncClient",
        return_value=_make_mock_client(),
    ):
        result = await OpenMeteoSolarGateway().get_solar_potential(
            latitude=-8.0476, longitude=-34.877
        )

    assert result.latitude == -8.0476
    assert result.longitude == -34.877


async def test_average_shortwave_radiation_is_positive() -> None:
    with patch(
        "solar_financing_assistant.infrastructure.gateways.open_meteo_solar_gateway.httpx.AsyncClient",
        return_value=_make_mock_client(),
    ):
        result = await OpenMeteoSolarGateway().get_solar_potential(
            latitude=-8.0476, longitude=-34.877
        )

    assert result.average_shortwave_radiation is not None
    assert result.average_shortwave_radiation > 0


async def test_estimated_daily_generation_is_positive() -> None:
    with patch(
        "solar_financing_assistant.infrastructure.gateways.open_meteo_solar_gateway.httpx.AsyncClient",
        return_value=_make_mock_client(),
    ):
        result = await OpenMeteoSolarGateway().get_solar_potential(
            latitude=-8.0476, longitude=-34.877
        )

    assert result.estimated_daily_generation_kwh_per_kwp > 0
