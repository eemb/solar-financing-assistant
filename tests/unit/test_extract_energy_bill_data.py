from decimal import Decimal
from pathlib import Path

import pytest

from solar_financing_assistant.application.use_cases.extract_energy_bill_data import (
    ExtractEnergyBillDataUseCase,
)
from solar_financing_assistant.domain.exceptions import InvalidEnergyBillError
from solar_financing_assistant.infrastructure.ocr.mock_ocr_adapter import MockOCRAdapter


async def test_extract_energy_bill_data_with_mock_ocr() -> None:
    ocr = MockOCRAdapter()
    use_case = ExtractEnergyBillDataUseCase(ocr)

    result = await use_case.execute(Path("fake-bill.pdf"))

    assert result.customer_name == "João da Silva"
    assert result.cpf == "12345678909"
    assert result.zipcode == "52000000"
    assert result.distributor == "Neoenergia Pernambuco"
    assert result.monthly_consumption_kwh == 450.0
    assert result.monthly_cost_brl == Decimal("380.50")
    assert result.tariff_brl_per_kwh == Decimal("0.8455")
    assert result.reference_month == "2026-05"


async def test_extract_energy_bill_data_raises_when_consumption_missing() -> None:
    from decimal import Decimal

    from solar_financing_assistant.application.dtos.extracted_energy_bill_data_dto import (
        ExtractedEnergyBillDataDTO,
    )
    from solar_financing_assistant.application.ports.ocr_port import OCRPort

    class _BlankOCR(OCRPort):
        async def extract_energy_bill_data(self, file_path: Path) -> ExtractedEnergyBillDataDTO:
            return ExtractedEnergyBillDataDTO(
                distributor="Any",
                monthly_consumption_kwh=None,
                monthly_cost_brl=Decimal("100.00"),
            )

    use_case = ExtractEnergyBillDataUseCase(_BlankOCR())
    with pytest.raises(InvalidEnergyBillError, match="consumption"):
        await use_case.execute(Path("fake.pdf"))
