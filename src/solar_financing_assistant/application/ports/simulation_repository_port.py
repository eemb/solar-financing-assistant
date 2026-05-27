from abc import ABC, abstractmethod

from solar_financing_assistant.domain.entities.financing_simulation import (
    FinancingSimulation,
)


class FinancingSimulationRepositoryPort(ABC):
    @abstractmethod
    async def save(self, simulation: FinancingSimulation) -> None:
        pass

    @abstractmethod
    async def find_by_id(self, simulation_id: str) -> FinancingSimulation | None:
        pass
