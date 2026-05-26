from decimal import Decimal

import pytest

from solar_financing_assistant.domain.exceptions import SimulationError
from solar_financing_assistant.infrastructure.financing.local_financing_engine import (
    LocalFinancingEngine,
)


def test_local_financing_engine_simulates_offer() -> None:
    engine = LocalFinancingEngine()

    offer = engine.simulate(
        project_cost=Decimal("22000.00"),
        number_of_installments=60,
        monthly_rate=Decimal("0.019"),
    )

    assert offer.approved_amount == Decimal("22000.00")
    assert offer.number_of_installments == 60
    assert offer.monthly_rate == Decimal("0.019")
    assert offer.installment_amount > 0
    assert offer.is_valid() is True


def test_local_financing_engine_rejects_invalid_project_cost() -> None:
    engine = LocalFinancingEngine()

    with pytest.raises(SimulationError):
        engine.simulate(
            project_cost=Decimal("0.00"),
            number_of_installments=60,
            monthly_rate=Decimal("0.019"),
        )
