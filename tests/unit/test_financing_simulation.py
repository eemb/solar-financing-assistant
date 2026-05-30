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
            document="12345678909",
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
        assert sim.offers == ()
        assert sim.get_best_offer() is None

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

    def test_get_best_offer_default_key_is_lowest_installment(self):
        sim = self._make_simulation()

        high_installment = FinancingOffer(
            approved_amount=Decimal("30000.00"),
            installment_amount=Decimal("800.00"),
            number_of_installments=60,
            monthly_rate=Decimal("0.015"),
        )
        low_installment = FinancingOffer(
            approved_amount=Decimal("25000.00"),
            installment_amount=Decimal("600.00"),
            number_of_installments=48,
            monthly_rate=Decimal("0.008"),
        )

        sim.add_offer(high_installment)
        sim.add_offer(low_installment)

        best = sim.get_best_offer()
        assert best is not None
        assert best.approved_amount == Decimal("25000.00")

    def test_get_best_offer_accepts_custom_key(self):
        sim = self._make_simulation()

        fewer_installments = FinancingOffer(
            approved_amount=Decimal("20000.00"),
            installment_amount=Decimal("900.00"),
            number_of_installments=24,
            monthly_rate=Decimal("0.012"),
        )
        more_installments = FinancingOffer(
            approved_amount=Decimal("20000.00"),
            installment_amount=Decimal("500.00"),
            number_of_installments=60,
            monthly_rate=Decimal("0.019"),
        )

        sim.add_offer(fewer_installments)
        sim.add_offer(more_installments)

        best_by_total = sim.get_best_offer(key=lambda o: o.total_cost)
        assert best_by_total is not None
        assert best_by_total.number_of_installments == 24

    def test_mark_approved(self):
        sim = self._make_simulation()
        sim.mark_approved()
        assert sim.status == SimulationStatus.APPROVED

    def test_mark_failed(self):
        sim = self._make_simulation()
        sim.mark_failed()
        assert sim.status == SimulationStatus.FAILED

    def test_solar_project_initially_none(self):
        sim = self._make_simulation()
        assert sim.solar_project is None
