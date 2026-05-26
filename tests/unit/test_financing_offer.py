import math

from solar_financing_assistant.domain.entities import FinancingOffer


class TestFinancingOffer:
    def _make_offer(self) -> FinancingOffer:
        return FinancingOffer(
            institution="Banco Solar",
            annual_interest_rate=0.12,
            term_months=60,
            monthly_payment_brl=600.0,
            financed_amount_brl=28000.0,
            down_payment_brl=2000.0,
        )

    def test_total_cost(self):
        offer = self._make_offer()
        expected = 2000.0 + (600.0 * 60)
        assert math.isclose(offer.total_cost_brl, expected)

    def test_total_interest(self):
        offer = self._make_offer()
        total_cost = 2000.0 + (600.0 * 60)
        expected_interest = total_cost - 2000.0 - 28000.0
        assert math.isclose(offer.total_interest_brl, expected_interest)

    def test_no_down_payment(self):
        offer = FinancingOffer(
            institution="Banco X",
            annual_interest_rate=0.10,
            term_months=48,
            monthly_payment_brl=700.0,
            financed_amount_brl=25000.0,
        )

        assert offer.down_payment_brl == 0.0
        assert math.isclose(offer.total_cost_brl, 700.0 * 48)
