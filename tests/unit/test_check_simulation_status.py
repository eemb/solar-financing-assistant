import pytest

from solar_financing_assistant.application.use_cases.check_simulation_status import (
    CheckSimulationStatusUseCase,
)
from solar_financing_assistant.domain.entities.financing_simulation import FinancingSimulation
from solar_financing_assistant.domain.exceptions import SimulationError
from solar_financing_assistant.infrastructure.repositories.in_memory_simulation_repository import (
    InMemorySimulationRepository,
)


def test_returns_existing_simulation() -> None:
    repo = InMemorySimulationRepository()
    simulation = FinancingSimulation(simulation_id="SIM-42")
    repo.save(simulation)

    use_case = CheckSimulationStatusUseCase(repo)
    result = use_case.execute("SIM-42")

    assert result is simulation


def test_raises_simulation_error_when_not_found() -> None:
    repo = InMemorySimulationRepository()
    use_case = CheckSimulationStatusUseCase(repo)

    with pytest.raises(SimulationError, match="Simulation not found."):
        use_case.execute("SIM-MISSING")
