from pathlib import Path

from solar_financing_assistant.application.dtos.extracted_energy_bill_data_dto import (
    ExtractedEnergyBillDataDTO,
)
from solar_financing_assistant.application.ports.ocr_port import OCRPort
from solar_financing_assistant.domain.exceptions import InvalidEnergyBillError


class ExtractEnergyBillDataUseCase:
    def __init__(self, ocr: OCRPort) -> None:
        self.ocr = ocr

    async def execute(self, file_path: Path) -> ExtractedEnergyBillDataDTO:
        dto = await self.ocr.extract_energy_bill_data(file_path)

        if dto.monthly_consumption_kwh is None or dto.monthly_consumption_kwh <= 0:
            raise InvalidEnergyBillError(
                "Monthly consumption must be present and greater than zero."
            )

        if dto.monthly_cost_brl is None or dto.monthly_cost_brl <= 0:
            raise InvalidEnergyBillError(
                "Monthly cost must be present and greater than zero."
            )

        if dto.distributor is None or not dto.distributor.strip():
            raise InvalidEnergyBillError("Distributor name must be present.")

        return dto
