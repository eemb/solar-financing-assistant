from solar_financing_assistant.domain.entities.financing_simulation import FinancingSimulation
from solar_financing_assistant.infrastructure.repositories.in_memory_simulation_repository import (
    InMemorySimulationRepository,
)


def test_save_and_find_by_id() -> None:
    repo = InMemorySimulationRepository()
    simulation = FinancingSimulation(simulation_id="SIM-001")

    repo.save(simulation)

    result = repo.find_by_id("SIM-001")
    assert result is simulation


def test_find_by_id_returns_none_when_not_found() -> None:
    repo = InMemorySimulationRepository()

    result = repo.find_by_id("SIM-NONEXISTENT")
    assert result is None
