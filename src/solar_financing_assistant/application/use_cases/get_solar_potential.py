"""Use case: fetch solar potential for a given coordinate."""

from solar_financing_assistant.application.dtos.solar_potential_dto import SolarPotentialDTO
from solar_financing_assistant.application.ports.solar_potential_gateway_port import (
    SolarPotentialGatewayPort,
)
from solar_financing_assistant.domain.exceptions import SimulationError


class GetSolarPotentialUseCase:
    def __init__(self, solar_potential_gateway: SolarPotentialGatewayPort) -> None:
        self.solar_potential_gateway = solar_potential_gateway

    async def execute(self, latitude: float, longitude: float) -> SolarPotentialDTO:
        if not (-90 <= latitude <= 90):
            raise SimulationError(f"Invalid latitude: {latitude}. Must be between -90 and 90.")
        if not (-180 <= longitude <= 180):
            raise SimulationError(f"Invalid longitude: {longitude}. Must be between -180 and 180.")

        return await self.solar_potential_gateway.get_solar_potential(latitude, longitude)
