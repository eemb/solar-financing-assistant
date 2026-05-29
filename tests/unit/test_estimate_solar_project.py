"""Unit tests for EstimateSolarProjectUseCase."""

from decimal import Decimal

import pytest

from solar_financing_assistant.application.dtos.solar_project_estimate_input_dto import (
    SolarProjectEstimateInputDTO,
)
from solar_financing_assistant.application.use_cases.estimate_solar_project import (
    EstimateSolarProjectUseCase,
)
from solar_financing_assistant.domain.exceptions import SimulationError


@pytest.fixture()
def use_case() -> EstimateSolarProjectUseCase:
    return EstimateSolarProjectUseCase()


def _make_input(
    monthly_consumption_kwh: float = 450.0,
    generation_per_kwp_month: float = 120.0,
    cost_per_kwp_brl: Decimal = Decimal("5000.00"),
) -> SolarProjectEstimateInputDTO:
    return SolarProjectEstimateInputDTO(
        monthly_consumption_kwh=monthly_consumption_kwh,
        generation_per_kwp_month=generation_per_kwp_month,
        cost_per_kwp_brl=cost_per_kwp_brl,
    )


def test_estimates_solar_project_correctly(use_case: EstimateSolarProjectUseCase) -> None:
    result = use_case.execute(_make_input())

    assert result.estimated_system_kwp == pytest.approx(3.75)
    assert result.estimated_monthly_generation_kwh == pytest.approx(450.0)
    assert result.estimated_project_cost == Decimal("18750.00")


def test_estimated_system_kwp_value(use_case: EstimateSolarProjectUseCase) -> None:
    result = use_case.execute(_make_input(monthly_consumption_kwh=450.0))
    assert result.estimated_system_kwp == pytest.approx(450.0 / 120.0)


def test_monthly_consumption_zero_raises(use_case: EstimateSolarProjectUseCase) -> None:
    with pytest.raises(SimulationError):
        use_case.execute(_make_input(monthly_consumption_kwh=0))


def test_generation_per_kwp_month_zero_raises(use_case: EstimateSolarProjectUseCase) -> None:
    with pytest.raises(SimulationError):
        use_case.execute(_make_input(generation_per_kwp_month=0))


def test_cost_per_kwp_brl_zero_raises(use_case: EstimateSolarProjectUseCase) -> None:
    with pytest.raises(SimulationError):
        use_case.execute(_make_input(cost_per_kwp_brl=Decimal("0")))
