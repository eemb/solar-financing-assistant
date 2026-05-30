"""Open-Meteo implementation of SolarPotentialGatewayPort."""

import httpx

from solar_financing_assistant.application.dtos.solar_potential_dto import SolarPotentialDTO
from solar_financing_assistant.application.ports.solar_potential_gateway_port import (
    SolarPotentialGatewayPort,
)
from solar_financing_assistant.domain.exceptions import SimulationError


class OpenMeteoSolarGateway(SolarPotentialGatewayPort):
    def __init__(
        self,
        base_url: str = "https://api.open-meteo.com/v1/forecast",
        timeout_seconds: float = 10.0,
        performance_ratio: float = 0.75,
    ) -> None:
        self.base_url = base_url
        self._performance_ratio = performance_ratio
        self._client = httpx.AsyncClient(timeout=timeout_seconds)

    async def aclose(self) -> None:
        await self._client.aclose()

    async def get_solar_potential(self, latitude: float, longitude: float) -> SolarPotentialDTO:
        response = await self._client.get(
            self.base_url,
            params={
                "latitude": latitude,
                "longitude": longitude,
                "hourly": "shortwave_radiation",
                "forecast_days": 1,
                "timezone": "auto",
            },
        )
        response.raise_for_status()

        data: dict = response.json()
        raw_values: list = data["hourly"]["shortwave_radiation"]

        radiation_values = [v for v in raw_values if isinstance(v, (int, float))]

        if not radiation_values:
            raise SimulationError("Solar radiation data not available.")

        average_shortwave_radiation = sum(radiation_values) / len(radiation_values)

        daily_irradiation_kwh_m2 = sum(radiation_values) / 1000
        estimated_daily_generation_kwh_per_kwp = daily_irradiation_kwh_m2 * self._performance_ratio

        return SolarPotentialDTO(
            latitude=latitude,
            longitude=longitude,
            average_shortwave_radiation=round(average_shortwave_radiation, 2),
            estimated_daily_generation_kwh_per_kwp=round(estimated_daily_generation_kwh_per_kwp, 2),
        )
