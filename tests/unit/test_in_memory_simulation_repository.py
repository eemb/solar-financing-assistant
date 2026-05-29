from uuid import uuid4

from solar_financing_assistant.domain.entities.financing_simulation import FinancingSimulation
from solar_financing_assistant.infrastructure.repositories.in_memory_simulation_repository import (
    InMemorySimulationRepository,
)


def test_save_and_find_by_id() -> None:
    repo = InMemorySimulationRepository()
    simulation = FinancingSimulation()

    repo.save(simulation)

    result = repo.find_by_id(simulation.id)
    assert result is simulation


def test_find_by_id_returns_none_when_not_found() -> None:
    repo = InMemorySimulationRepository()

    result = repo.find_by_id(uuid4())
    assert result is None
