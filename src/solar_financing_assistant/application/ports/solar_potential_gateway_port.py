from abc import ABC, abstractmethod

from solar_financing_assistant.application.dtos.solar_potential_dto import SolarPotentialDTO


class SolarPotentialGatewayPort(ABC):
    @abstractmethod
    def get_solar_potential(
        self,
        latitude: float,
        longitude: float,
    ) -> SolarPotentialDTO:
        pass
