"""FinancingAssistantTools — thin orchestration layer exposing use cases as tool methods.

Each method returns a plain dict suitable for JSON serialisation; no business
logic lives here.  Domain exceptions are caught and surfaced as error dicts so
callers (e.g. an LLM agent) can handle them gracefully.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from uuid import UUID

from solar_financing_assistant.application.dtos.extracted_energy_bill_data_dto import (
    ExtractedEnergyBillDataDTO,
)
from solar_financing_assistant.application.use_cases.check_simulation_status import (
    CheckSimulationStatusUseCase,
)
from solar_financing_assistant.application.use_cases.complete_energy_bill_data import (
    CompleteEnergyBillDataUseCase,
)
from solar_financing_assistant.application.use_cases.create_financing_simulation import (
    CreateFinancingSimulationUseCase,
)
from solar_financing_assistant.application.use_cases.estimate_solar_project_from_bill import (
    EstimateSolarProjectFromBillUseCase,
)
from solar_financing_assistant.application.use_cases.extract_energy_bill_data import (
    ExtractEnergyBillDataUseCase,
)
from solar_financing_assistant.application.use_cases.get_missing_energy_bill_fields import (
    GetMissingEnergyBillFieldsUseCase,
)
from solar_financing_assistant.domain.entities.financing_offer import FinancingOffer
from solar_financing_assistant.domain.entities.financing_simulation import FinancingSimulation
from solar_financing_assistant.domain.entities.solar_project import SolarProject
from solar_financing_assistant.domain.exceptions import DomainError

# ---------------------------------------------------------------------------
# Private serialisation helpers
# ---------------------------------------------------------------------------

_STATUS_MESSAGES: dict[str, str] = {
    "approved": "Simulação aprovada com oferta de financiamento.",
    "failed": "Simulação reprovada.",
    "created": "Simulação criada.",
    "pending": "Simulação pendente.",
    "in_progress": "Simulação em andamento.",
}


def _solar_project_to_dict(project: SolarProject) -> dict:
    return {
        "id": str(project.id),
        "monthly_consumption_kwh": project.monthly_consumption_kwh,
        "estimated_system_kwp": project.estimated_system_kwp,
        "estimated_monthly_generation_kwh": project.estimated_monthly_generation_kwh,
        "estimated_project_cost": str(project.estimated_project_cost),
    }


def _offer_to_dict(offer: FinancingOffer) -> dict:
    return {
        "id": str(offer.id),
        "approved_amount": str(offer.approved_amount),
        "installment_amount": str(offer.installment_amount),
        "number_of_installments": offer.number_of_installments,
        "monthly_rate": str(offer.monthly_rate),
        "total_cost": str(offer.total_cost),
    }


def _simulation_to_dict(
    simulation: FinancingSimulation,
    solar_potential_source: str = "unknown",
) -> dict:
    status = simulation.status.value
    offer = simulation.get_best_offer()
    return {
        "simulation_id": str(simulation.id),
        "status": status,
        "message": _STATUS_MESSAGES.get(status, "Status desconhecido."),
        "solar_potential_source": solar_potential_source,
        "solar_potential_fallback_warning": (
            "O potencial solar real não pôde ser consultado. "
            "A estimativa usou o valor padrão de geração (fallback). "
            "Os resultados podem variar com dados reais de irradiação solar."
        )
        if solar_potential_source == "fallback"
        else None,
        "solar_project": _solar_project_to_dict(simulation.solar_project)
        if simulation.solar_project
        else None,
        "offer": _offer_to_dict(offer) if offer else None,
    }


# ---------------------------------------------------------------------------
# Public tool class
# ---------------------------------------------------------------------------


class FinancingAssistantTools:
    """Thin orchestration layer — wraps domain use cases for LLM-agent consumption.

    Methods intentionally contain no business logic; they only convert types,
    call use cases in order, and serialise the results to plain dicts.
    """

    def __init__(
        self,
        extract_energy_bill_data_use_case: ExtractEnergyBillDataUseCase,
        get_missing_energy_bill_fields_use_case: GetMissingEnergyBillFieldsUseCase,
        complete_energy_bill_data_use_case: CompleteEnergyBillDataUseCase,
        estimate_solar_project_from_bill_use_case: EstimateSolarProjectFromBillUseCase,
        create_financing_simulation_use_case: CreateFinancingSimulationUseCase,
        check_simulation_status_use_case: CheckSimulationStatusUseCase,
        monthly_rate: Decimal,
        ocr_provider_name: str = "ocr",
    ) -> None:
        self._extract_bill = extract_energy_bill_data_use_case
        self._get_missing = get_missing_energy_bill_fields_use_case
        self._complete_bill = complete_energy_bill_data_use_case
        self._estimate_project = estimate_solar_project_from_bill_use_case
        self._create_simulation = create_financing_simulation_use_case
        self._check_status = check_simulation_status_use_case
        self.monthly_rate = monthly_rate
        self._ocr_provider_name = ocr_provider_name

    # ------------------------------------------------------------------
    # Tool 1 — extract_energy_bill_data
    # ------------------------------------------------------------------

    async def extract_energy_bill_data(self, file_path: str) -> dict:
        """Extract bill data from an image/PDF and report which fields are missing."""
        path = Path(file_path)
        if not path.exists():
            return {"status": "error", "message": f"Arquivo não encontrado: {file_path}"}

        try:
            extracted_bill = await self._extract_bill.execute(path)
        except (DomainError, FileNotFoundError) as exc:
            return {"status": "error", "message": str(exc)}

        missing_fields = self._get_missing.execute(extracted_bill)
        result: dict = {
            "data": extracted_bill.model_dump(mode="json"),
            "missing_fields": missing_fields,
            "data_source": self._ocr_provider_name,
        }
        if self._ocr_provider_name == "mock":
            result["mock_data_warning"] = (
                "ATENÇÃO: Os dados retornados são FICTÍCIOS (gerados pelo MockOCRAdapter). "
                "Eles NÃO foram extraídos da conta real enviada pelo usuário. "
                "Informe claramente ao usuário que os dados são de exemplo antes de prosseguir."
            )
        return result

    # ------------------------------------------------------------------
    # Tool 2 — complete_energy_bill_data
    # ------------------------------------------------------------------

    def complete_energy_bill_data(
        self,
        extracted_bill_data: dict,
        manual_values: dict[str, str],
    ) -> dict:
        """Merge OCR-extracted data with manually supplied field values."""
        try:
            extracted_bill = ExtractedEnergyBillDataDTO(**extracted_bill_data)
            completed_bill = self._complete_bill.execute(extracted_bill, manual_values)
        except DomainError as exc:
            return {"status": "error", "message": str(exc)}

        missing_fields = self._get_missing.execute(completed_bill)
        return {
            "data": completed_bill.model_dump(mode="json"),
            "missing_fields": missing_fields,
        }

    # ------------------------------------------------------------------
    # Tool 3 — simulate_financing_from_bill
    # ------------------------------------------------------------------

    async def simulate_financing_from_bill(self, extracted_bill_data: dict) -> dict:
        """Run the full financing simulation pipeline from a bill data dict."""
        try:
            extracted_bill = ExtractedEnergyBillDataDTO(**extracted_bill_data)
        except Exception as exc:
            return {"status": "error", "message": str(exc)}

        missing_fields = self._get_missing.execute(extracted_bill)
        if missing_fields:
            return {"status": "missing_fields", "missing_fields": missing_fields}

        try:
            project_result = await self._estimate_project.execute_with_metadata(extracted_bill)
            solar_project, solar_potential_source = project_result
            simulation = self._create_simulation.execute(
                solar_project,
                monthly_rate=self.monthly_rate,
            )
        except DomainError as exc:
            return {"status": "error", "message": str(exc)}

        return _simulation_to_dict(simulation, solar_potential_source=solar_potential_source)

    # ------------------------------------------------------------------
    # Tool 4 — check_simulation_status
    # ------------------------------------------------------------------

    def check_simulation_status(self, simulation_id: str) -> dict:
        """Retrieve the current status of a previously created simulation."""
        try:
            sim_uuid = UUID(simulation_id)
        except ValueError:
            return {
                "status": "error",
                "message": f"Invalid simulation ID: {simulation_id!r}",
            }

        try:
            simulation = self._check_status.execute(sim_uuid)
        except DomainError as exc:
            return {"status": "error", "message": str(exc)}

        return _simulation_to_dict(simulation)
