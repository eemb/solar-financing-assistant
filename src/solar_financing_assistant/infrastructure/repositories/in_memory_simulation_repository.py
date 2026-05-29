"""In-memory implementation of FinancingSimulationRepositoryPort."""

from uuid import UUID

from solar_financing_assistant.application.ports.simulation_repository_port import (
    FinancingSimulationRepositoryPort,
)
from solar_financing_assistant.domain.entities.financing_simulation import FinancingSimulation


class InMemorySimulationRepository(FinancingSimulationRepositoryPort):
    def __init__(self) -> None:
        self._store: dict[UUID, FinancingSimulation] = {}

    def save(self, simulation: FinancingSimulation) -> None:
        self._store[simulation.id] = simulation

    def find_by_id(self, id: UUID) -> FinancingSimulation | None:
        return self._store.get(id)
