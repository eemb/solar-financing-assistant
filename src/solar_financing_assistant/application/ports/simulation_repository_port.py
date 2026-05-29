from typing import Protocol, runtime_checkable
from uuid import UUID

from solar_financing_assistant.domain.entities.financing_simulation import (
    FinancingSimulation,
)


@runtime_checkable
class FinancingSimulationRepositoryPort(Protocol):
    def save(self, simulation: FinancingSimulation) -> None: ...

    def find_by_id(self, id: UUID) -> FinancingSimulation | None: ...
