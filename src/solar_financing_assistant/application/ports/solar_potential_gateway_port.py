from typing import Protocol, runtime_checkable

from solar_financing_assistant.application.dtos.solar_potential_dto import SolarPotentialDTO


@runtime_checkable
class SolarPotentialGatewayPort(Protocol):
    def get_solar_potential(
        self,
        latitude: float,
        longitude: float,
    ) -> SolarPotentialDTO: ...
