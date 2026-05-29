from pathlib import Path
from typing import Protocol, runtime_checkable

from solar_financing_assistant.application.dtos.extracted_energy_bill_data_dto import (
    ExtractedEnergyBillDataDTO,
)


@runtime_checkable
class OCRPort(Protocol):
    async def extract_energy_bill_data(self, file_path: Path) -> ExtractedEnergyBillDataDTO: ...
