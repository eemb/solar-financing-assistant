"""Integration tests for LocalFinancingEngine.

These tests exercise the Price (French amortisation) formula end-to-end with
realistic financing values.  They guard against silent rounding drift that can
accumulate when the formula is refactored or the Decimal precision changes.
"""

from decimal import Decimal

import pytest

from solar_financing_assistant.domain.exceptions import SimulationError
from solar_financing_assistant.infrastructure.financing.local_financing_engine import (
    LocalFinancingEngine,
)


@pytest.fixture()
def engine() -> LocalFinancingEngine:
    return LocalFinancingEngine()


class TestPriceFormulaAccuracy:
    def test_standard_60_installments(self, engine: LocalFinancingEngine) -> None:
        """R$ 22 000 at 1.9 %/month over 60 months — reference value from a
        Brazilian financing calculator."""
        offer = engine.simulate(
            project_cost=Decimal("22000.00"),
            number_of_installments=60,
            monthly_rate=Decimal("0.019"),
        )

        assert offer.approved_amount == Decimal("22000.00")
        assert offer.number_of_installments == 60
        assert offer.monthly_rate == Decimal("0.019")
        # Calculated reference: ≈ R$ 617.67
        assert offer.installment_amount == Decimal("617.67")

    def test_total_cost_exceeds_principal(self, engine: LocalFinancingEngine) -> None:
        """Total repayment must always be greater than the principal when rate > 0."""
        offer = engine.simulate(
            project_cost=Decimal("15000.00"),
            number_of_installments=36,
            monthly_rate=Decimal("0.019"),
        )

        assert offer.total_cost > offer.approved_amount

    def test_zero_rate_yields_equal_installments(self, engine: LocalFinancingEngine) -> None:
        """With monthly_rate=0 each installment must equal principal / n exactly."""
        offer = engine.simulate(
            project_cost=Decimal("12000.00"),
            number_of_installments=12,
            monthly_rate=Decimal("0"),
        )

        assert offer.installment_amount == Decimal("1000.00")
        assert offer.total_cost == Decimal("12000.00")

    def test_rounding_does_not_drift_across_term_lengths(
        self, engine: LocalFinancingEngine
    ) -> None:
        """The installment amount must not grow with term length for the same
        principal and rate (longer terms → lower monthly payment)."""
        offer_24 = engine.simulate(
            project_cost=Decimal("20000.00"),
            number_of_installments=24,
            monthly_rate=Decimal("0.019"),
        )
        offer_60 = engine.simulate(
            project_cost=Decimal("20000.00"),
            number_of_installments=60,
            monthly_rate=Decimal("0.019"),
        )

        assert offer_60.installment_amount < offer_24.installment_amount

    def test_offer_is_always_valid(self, engine: LocalFinancingEngine) -> None:
        """Every offer produced by the engine must pass its own invariant check."""
        for n in (12, 24, 36, 48, 60):
            offer = engine.simulate(
                project_cost=Decimal("18000.00"),
                number_of_installments=n,
                monthly_rate=Decimal("0.019"),
            )
            assert offer.is_valid(), f"Offer for {n} installments failed is_valid()"

    def test_large_project_cost(self, engine: LocalFinancingEngine) -> None:
        """Engine handles a large project (R$ 200 000) without overflow or precision loss."""
        offer = engine.simulate(
            project_cost=Decimal("200000.00"),
            number_of_installments=60,
            monthly_rate=Decimal("0.019"),
        )

        assert offer.approved_amount == Decimal("200000.00")
        assert offer.installment_amount > 0
        assert offer.total_cost > Decimal("200000.00")


class TestEngineValidation:
    def test_rejects_zero_project_cost(self, engine: LocalFinancingEngine) -> None:
        with pytest.raises(SimulationError, match="Project cost"):
            engine.simulate(
                project_cost=Decimal("0"),
                number_of_installments=60,
                monthly_rate=Decimal("0.019"),
            )

    def test_rejects_negative_project_cost(self, engine: LocalFinancingEngine) -> None:
        with pytest.raises(SimulationError, match="Project cost"):
            engine.simulate(
                project_cost=Decimal("-1000.00"),
                number_of_installments=60,
                monthly_rate=Decimal("0.019"),
            )

    def test_rejects_zero_installments(self, engine: LocalFinancingEngine) -> None:
        with pytest.raises(SimulationError, match="installments"):
            engine.simulate(
                project_cost=Decimal("10000.00"),
                number_of_installments=0,
                monthly_rate=Decimal("0.019"),
            )

    def test_rejects_negative_rate(self, engine: LocalFinancingEngine) -> None:
        with pytest.raises(SimulationError, match="rate"):
            engine.simulate(
                project_cost=Decimal("10000.00"),
                number_of_installments=60,
                monthly_rate=Decimal("-0.001"),
            )
