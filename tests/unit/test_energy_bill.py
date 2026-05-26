from solar_financing_assistant.domain.entities import EnergyBill


class TestEnergyBill:
    def _make_bill(self) -> EnergyBill:
        return EnergyBill(
            monthly_consumption_kwh=350.0,
            monthly_cost_brl=280.0,
            distributor="CPFL",
            tariff_brl_per_kwh=0.80,
            reference_month="2025-03",
        )

    def test_annual_consumption(self):
        bill = self._make_bill()
        assert bill.annual_consumption_kwh == 4200.0

    def test_annual_cost(self):
        bill = self._make_bill()
        assert bill.annual_cost_brl == 3360.0

    def test_frozen_instance(self):
        bill = self._make_bill()

        try:
            bill.monthly_consumption_kwh = 500.0  # type: ignore[misc]
            raise AssertionError("Should not allow mutation")
        except Exception:
            pass
