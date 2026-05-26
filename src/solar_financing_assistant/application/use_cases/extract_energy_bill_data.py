from pathlib import Path

from solar_financing_assistant.application.dtos.extracted_energy_bill_data_dto import (
    ExtractedEnergyBillDataDTO,
)
from solar_financing_assistant.application.ports.ocr_port import OCRPort


class ExtractEnergyBillDataUseCase:
    def __init__(self, ocr: OCRPort):
        self.ocr = ocr

    def execute(self, file_path: Path) -> ExtractedEnergyBillDataDTO:
        return self.ocr.extract_energy_bill_data(file_path)
