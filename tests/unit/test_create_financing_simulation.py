from decimal import Decimal

import pytest

from solar_financing_assistant.application.use_cases.create_financing_simulation import (
    CreateFinancingSimulationUseCase,
)
from solar_financing_assistant.domain.entities.financing_simulation import SimulationStatus
from solar_financing_assistant.domain.entities.solar_project import SolarProject
from solar_financing_assistant.domain.exceptions import SimulationError
from solar_financing_assistant.infrastructure.financing.local_financing_engine import (
    LocalFinancingEngine,
)
from solar_financing_assistant.infrastructure.repositories.in_memory_simulation_repository import (
    InMemorySimulationRepository,
)


def _make_viable_project() -> SolarProject:
    return SolarProject(
        monthly_consumption_kwh=450.0,
        estimated_system_kwp=3.8,
        estimated_monthly_generation_kwh=460.0,
        estimated_project_cost=Decimal("22000.00"),
    )


def test_creates_approved_simulation() -> None:
    use_case = CreateFinancingSimulationUseCase(
        LocalFinancingEngine(), InMemorySimulationRepository()
    )

    simulation = use_case.execute(_make_viable_project())

    assert simulation.status == SimulationStatus.APPROVED


def test_simulation_has_uuid_id() -> None:
    from uuid import UUID

    use_case = CreateFinancingSimulationUseCase(
        LocalFinancingEngine(), InMemorySimulationRepository()
    )

    simulation = use_case.execute(_make_viable_project())

    assert isinstance(simulation.id, UUID)


def test_saves_simulation_in_repository() -> None:
    repo = InMemorySimulationRepository()
    use_case = CreateFinancingSimulationUseCase(LocalFinancingEngine(), repo)

    simulation = use_case.execute(_make_viable_project())

    found = repo.find_by_id(simulation.id)
    assert found is simulation


def test_returns_non_null_offer() -> None:
    use_case = CreateFinancingSimulationUseCase(
        LocalFinancingEngine(), InMemorySimulationRepository()
    )

    simulation = use_case.execute(_make_viable_project())

    assert simulation.get_best_offer() is not None


def test_raises_error_for_non_viable_project() -> None:
    use_case = CreateFinancingSimulationUseCase(
        LocalFinancingEngine(), InMemorySimulationRepository()
    )
    non_viable = SolarProject(
        monthly_consumption_kwh=450.0,
        estimated_system_kwp=3.8,
        estimated_monthly_generation_kwh=0.0,
        estimated_project_cost=Decimal("22000.00"),
    )

    with pytest.raises(SimulationError, match="not viable"):
        use_case.execute(non_viable)
