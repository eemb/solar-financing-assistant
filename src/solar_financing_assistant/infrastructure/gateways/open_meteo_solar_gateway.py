"""Open-Meteo implementation of SolarPotentialGatewayPort.

Uses the Open-Meteo *archive* endpoint to derive an average daily solar
irradiation from the previous 12 months of historical data, giving a much
more stable estimate for solar system sizing than a single-day forecast.
"""

import logging
from datetime import date, timedelta
from typing import Any

import httpx

from solar_financing_assistant.application.dtos.solar_potential_dto import SolarPotentialDTO
from solar_financing_assistant.application.ports.solar_potential_gateway_port import (
    SolarPotentialGatewayPort,
)
from solar_financing_assistant.domain.exceptions import SimulationError

logger = logging.getLogger(__name__)

_ARCHIVE_BASE_URL = "https://archive-api.open-meteo.com/v1/archive"
_HISTORY_DAYS = 365


class OpenMeteoSolarGateway(SolarPotentialGatewayPort):
    def __init__(
        self,
        base_url: str = _ARCHIVE_BASE_URL,
        timeout_seconds: float = 10.0,
        performance_ratio: float = 0.75,
    ) -> None:
        self.base_url = base_url
        self._performance_ratio = performance_ratio
        self._client = httpx.AsyncClient(timeout=timeout_seconds)

    async def aclose(self) -> None:
        await self._client.aclose()

    async def get_solar_potential(self, latitude: float, longitude: float) -> SolarPotentialDTO:
        end_date = date.today() - timedelta(days=1)
        start_date = end_date - timedelta(days=_HISTORY_DAYS - 1)

        response = await self._client.get(
            self.base_url,
            params={
                "latitude": latitude,
                "longitude": longitude,
                "hourly": "shortwave_radiation",
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "timezone": "auto",
            },
        )
        response.raise_for_status()

        data: dict[str, Any] = response.json()
        raw_values: list[Any] = data["hourly"]["shortwave_radiation"]

        radiation_values = [v for v in raw_values if isinstance(v, (int, float))]

        if not radiation_values:
            raise SimulationError("Solar radiation data not available.")

        average_shortwave_radiation = sum(radiation_values) / len(radiation_values)

        # Total irradiation (Wh/m²) over the whole period → average daily (kWh/m²/day)
        total_irradiation_kwh_m2 = sum(radiation_values) / 1000
        average_daily_irradiation_kwh_m2 = total_irradiation_kwh_m2 / _HISTORY_DAYS
        estimated_daily_generation_kwh_per_kwp = (
            average_daily_irradiation_kwh_m2 * self._performance_ratio
        )

        logger.debug(
            "Solar potential (%.4f, %.4f): avg_daily=%.3f kWh/m²/day, "
            "est_gen=%.3f kWh/kWp/day [%s → %s, %d days]",
            latitude,
            longitude,
            average_daily_irradiation_kwh_m2,
            estimated_daily_generation_kwh_per_kwp,
            start_date,
            end_date,
            _HISTORY_DAYS,
        )

        return SolarPotentialDTO(
            latitude=latitude,
            longitude=longitude,
            average_shortwave_radiation=round(average_shortwave_radiation, 2),
            estimated_daily_generation_kwh_per_kwp=round(estimated_daily_generation_kwh_per_kwp, 4),
        )
