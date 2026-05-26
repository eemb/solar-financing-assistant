from decimal import Decimal

from solar_financing_assistant.application.use_cases.simulate_financing import (
    SimulateFinancingUseCase,
)
from solar_financing_assistant.domain.entities.solar_project import SolarProject
from solar_financing_assistant.infrastructure.financing.local_financing_engine import (
    LocalFinancingEngine,
)


def test_simulate_financing_use_case_returns_offer() -> None:
    project = SolarProject(
        monthly_consumption_kwh=450.0,
        estimated_system_kwp=3.8,
        estimated_monthly_generation_kwh=460.0,
        estimated_project_cost=Decimal("22000.00"),
    )

    use_case = SimulateFinancingUseCase(LocalFinancingEngine())

    offer = use_case.execute(project)

    assert offer.approved_amount == Decimal("22000.00")
    assert offer.installment_amount > 0
    assert offer.number_of_installments == 60
    assert offer.monthly_rate == Decimal("0.019")
