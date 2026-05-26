from decimal import Decimal
from pathlib import Path

from solar_financing_assistant.application.use_cases.extract_energy_bill_data import (
    ExtractEnergyBillDataUseCase,
)
from solar_financing_assistant.infrastructure.ocr.mock_ocr_adapter import MockOCRAdapter


def test_extract_energy_bill_data_with_mock_ocr() -> None:
    ocr = MockOCRAdapter()
    use_case = ExtractEnergyBillDataUseCase(ocr)

    result = use_case.execute(Path("fake-bill.pdf"))

    assert result.customer_name == "João da Silva"
    assert result.cpf == "12345678909"
    assert result.zipcode == "52000000"
    assert result.distributor == "Neoenergia Pernambuco"
    assert result.monthly_consumption_kwh == 450.0
    assert result.monthly_cost_brl == Decimal("380.50")
    assert result.tariff_brl_per_kwh == Decimal("0.8455")
    assert result.reference_month == "2026-05"
