from decimal import Decimal

from solar_financing_assistant.domain.entities import FinancingOffer


class TestFinancingOffer:
    def _make_offer(self) -> FinancingOffer:
        return FinancingOffer(
            approved_amount=Decimal("28000.00"),
            installment_amount=Decimal("600.00"),
            number_of_installments=60,
            monthly_rate=Decimal("0.012"),
        )

    def test_total_cost(self):
        offer = self._make_offer()
        expected = Decimal("600.00") * 60
        assert offer.total_cost == expected

    def test_is_valid(self):
        offer = self._make_offer()
        assert offer.is_valid() is True

    def test_is_not_valid_zero_amount(self):
        offer = FinancingOffer(
            approved_amount=Decimal("0"),
            installment_amount=Decimal("600.00"),
            number_of_installments=60,
            monthly_rate=Decimal("0.012"),
        )
        assert offer.is_valid() is False
