from decimal import Decimal
from pathlib import Path

from solar_financing_assistant.application.dtos.extracted_energy_bill_data_dto import (
    ExtractedEnergyBillDataDTO,
)
from solar_financing_assistant.application.ports.ocr_port import OCRPort


class MockOCRAdapter(OCRPort):
    async def extract_energy_bill_data(self, file_path: Path) -> ExtractedEnergyBillDataDTO:
        if not file_path.exists():
            raise FileNotFoundError(f"Energy bill file not found: {file_path}")

        return ExtractedEnergyBillDataDTO(
            customer_name="João da Silva",
            cpf="12345678909",
            zipcode="52000000",
            distributor="Neoenergia Pernambuco",
            monthly_consumption_kwh=450.0,
            monthly_cost_brl=Decimal("380.50"),
            tariff_brl_per_kwh=Decimal("0.8455"),
            reference_month="2026-05",
        )
