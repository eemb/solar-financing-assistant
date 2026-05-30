"""Driving-side port protocols — use-case interfaces consumed by the interface layer."""

from decimal import Decimal
from pathlib import Path
from typing import Protocol, runtime_checkable
from uuid import UUID

from solar_financing_assistant.application.dtos.extracted_energy_bill_data_dto import (
    ExtractedEnergyBillDataDTO,
)
from solar_financing_assistant.domain.entities.financing_simulation import FinancingSimulation
from solar_financing_assistant.domain.entities.solar_project import SolarProject


@runtime_checkable
class ExtractEnergyBillDataPort(Protocol):
    async def execute(self, file_path: Path) -> ExtractedEnergyBillDataDTO: ...


@runtime_checkable
class CreateFinancingSimulationPort(Protocol):
    def execute(
        self,
        solar_project: SolarProject,
        number_of_installments: int,
        monthly_rate: Decimal,
    ) -> FinancingSimulation: ...


@runtime_checkable
class CheckSimulationStatusPort(Protocol):
    def execute(self, id: UUID) -> FinancingSimulation: ...


@runtime_checkable
class EstimateSolarProjectFromBillPort(Protocol):
    async def execute(self, extracted_bill: ExtractedEnergyBillDataDTO) -> SolarProject: ...


@runtime_checkable
class GetMissingEnergyBillFieldsPort(Protocol):
    def execute(self, extracted_bill: ExtractedEnergyBillDataDTO) -> list[str]: ...


@runtime_checkable
class CompleteEnergyBillDataPort(Protocol):
    def execute(
        self,
        extracted_bill: ExtractedEnergyBillDataDTO,
        manual_values: dict[str, str],
    ) -> ExtractedEnergyBillDataDTO: ...
