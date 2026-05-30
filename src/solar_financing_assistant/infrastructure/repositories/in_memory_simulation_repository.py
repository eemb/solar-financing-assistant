"""In-memory implementation of FinancingSimulationRepositoryPort."""

import logging
from uuid import UUID

from solar_financing_assistant.application.ports.simulation_repository_port import (
    FinancingSimulationRepositoryPort,
)
from solar_financing_assistant.domain.entities.financing_simulation import FinancingSimulation

logger = logging.getLogger(__name__)

_DEFAULT_MAX_SIZE = 1_000


class InMemorySimulationRepository(FinancingSimulationRepositoryPort):
    def __init__(self, max_size: int = _DEFAULT_MAX_SIZE) -> None:
        if max_size < 1:
            raise ValueError("max_size must be at least 1.")
        self._store: dict[UUID, FinancingSimulation] = {}
        self._max_size = max_size

    def save(self, simulation: FinancingSimulation) -> None:
        if simulation.id in self._store:
            self._store[simulation.id] = simulation
            return
        if len(self._store) >= self._max_size:
            oldest_key = next(iter(self._store))
            del self._store[oldest_key]
            logger.warning(
                "InMemorySimulationRepository reached max_size=%d; evicted oldest entry.",
                self._max_size,
            )
        self._store[simulation.id] = simulation

    def find_by_id(self, id: UUID) -> FinancingSimulation | None:
        return self._store.get(id)
