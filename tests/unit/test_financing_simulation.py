from decimal import Decimal

from solar_financing_assistant.domain.entities import (
    Customer,
    EnergyBill,
    FinancingOffer,
    FinancingSimulation,
)
from solar_financing_assistant.domain.entities.financing_simulation import SimulationStatus


class TestFinancingSimulation:
    def _make_simulation(self) -> FinancingSimulation:
        customer = Customer(
            name="João",
            document="111.222.333-44",
            email="joao@test.com",
            phone="11999990000",
        )
        bill = EnergyBill(
            monthly_consumption_kwh=400.0,
            monthly_cost_brl=320.0,
            distributor="Enel",
            tariff_brl_per_kwh=0.80,
            reference_month="2025-04",
        )
        return FinancingSimulation(customer=customer, energy_bill=bill)

    def test_initial_status_is_pending(self):
        sim = self._make_simulation()
        assert sim.status == SimulationStatus.PENDING

    def test_no_offers_initially(self):
        sim = self._make_simulation()
        assert sim.offers == []
        assert sim.best_offer is None

    def test_add_offer(self):
        sim = self._make_simulation()
        offer = FinancingOffer(
            approved_amount=Decimal("25000.00"),
            installment_amount=Decimal("650.00"),
            number_of_installments=48,
            monthly_rate=Decimal("0.010"),
        )
        sim.add_offer(offer)

        assert len(sim.offers) == 1
        assert sim.offers[0].approved_amount == Decimal("25000.00")

    def test_best_offer_returns_lowest_total_cost(self):
        sim = self._make_simulation()

        expensive = FinancingOffer(
            approved_amount=Decimal("30000.00"),
            installment_amount=Decimal("800.00"),
            number_of_installments=60,
            monthly_rate=Decimal("0.015"),
        )
        cheap = FinancingOffer(
            approved_amount=Decimal("25000.00"),
            installment_amount=Decimal("600.00"),
            number_of_installments=48,
            monthly_rate=Decimal("0.008"),
        )

        sim.add_offer(expensive)
        sim.add_offer(cheap)

        assert sim.best_offer is not None
        assert sim.best_offer.approved_amount == Decimal("25000.00")

    def test_mark_completed(self):
        sim = self._make_simulation()
        sim.mark_completed()
        assert sim.status == SimulationStatus.COMPLETED

    def test_mark_failed(self):
        sim = self._make_simulation()
        sim.mark_failed()
        assert sim.status == SimulationStatus.FAILED

    def test_solar_project_initially_none(self):
        sim = self._make_simulation()
        assert sim.solar_project is None
