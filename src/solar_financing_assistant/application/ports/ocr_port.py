from abc import ABC, abstractmethod
from pathlib import Path

from solar_financing_assistant.application.dtos.extracted_energy_bill_data_dto import (
    ExtractedEnergyBillDataDTO,
)


class OCRPort(ABC):
    @abstractmethod
    def extract_energy_bill_data(self, file_path: Path) -> ExtractedEnergyBillDataDTO:
        pass
