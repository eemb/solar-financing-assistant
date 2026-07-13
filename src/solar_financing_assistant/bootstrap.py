"""Application bootstrap — assembles FinancingAssistantTools from Settings.

Centralises the composition root so it can be shared between __main__.py
(CLI / AgentCLI entry point) and the FastAPI application without duplication.
"""

from solar_financing_assistant.application.use_cases.check_simulation_status import (
    CheckSimulationStatusUseCase,
)
from solar_financing_assistant.application.use_cases.complete_energy_bill_data import (
    CompleteEnergyBillDataUseCase,
)
from solar_financing_assistant.application.use_cases.create_financing_simulation import (
    CreateFinancingSimulationUseCase,
)
from solar_financing_assistant.application.use_cases.estimate_solar_project import (
    EstimateSolarProjectUseCase,
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
from solar_financing_assistant.application.use_cases.get_solar_potential import (
    GetSolarPotentialUseCase,
)
from solar_financing_assistant.application.use_cases.validate_address import (
    ValidateAddressUseCase,
)
from solar_financing_assistant.config.settings import Settings
from solar_financing_assistant.infrastructure.financing.local_financing_engine import (
    LocalFinancingEngine,
)
from solar_financing_assistant.infrastructure.gateways.brasilapi_address_gateway import (
    BrasilApiAddressGateway,
)
from solar_financing_assistant.infrastructure.gateways.open_meteo_solar_gateway import (
    OpenMeteoSolarGateway,
)
from solar_financing_assistant.infrastructure.llm.tools import FinancingAssistantTools
from solar_financing_assistant.infrastructure.ocr.ocr_adapter_factory import create_ocr_adapter
from solar_financing_assistant.infrastructure.repositories.in_memory_simulation_repository import (
    InMemorySimulationRepository,
)


def build_tools(app_settings: Settings) -> FinancingAssistantTools:
    """Construct :class:`FinancingAssistantTools` with all required use cases.

    A fresh :class:`InMemorySimulationRepository` is created on each call, so
    callers that want a singleton repository (e.g. the FastAPI app) should
    store the result and reuse it rather than calling this function repeatedly.
    """
    repository = InMemorySimulationRepository()
    ocr_adapter = create_ocr_adapter(app_settings.ocr_provider)

    address_gateway = BrasilApiAddressGateway(
        timeout_seconds=app_settings.http_timeout_seconds,
    )
    solar_gateway = OpenMeteoSolarGateway(
        timeout_seconds=app_settings.http_timeout_seconds,
        performance_ratio=app_settings.performance_ratio,
    )

    validate_address = ValidateAddressUseCase(address_gateway)
    get_solar_potential = GetSolarPotentialUseCase(solar_gateway)
    estimate_solar_project = EstimateSolarProjectUseCase()

    estimate_from_bill = EstimateSolarProjectFromBillUseCase(
        validate_address_use_case=validate_address,
        get_solar_potential_use_case=get_solar_potential,
        estimate_solar_project_use_case=estimate_solar_project,
        fallback_generation_per_kwp_month=app_settings.generation_per_kwp_month,
        cost_per_kwp_brl=app_settings.cost_per_kwp_brl,
    )

    return FinancingAssistantTools(
        extract_energy_bill_data_use_case=ExtractEnergyBillDataUseCase(ocr_adapter),
        get_missing_energy_bill_fields_use_case=GetMissingEnergyBillFieldsUseCase(),
        complete_energy_bill_data_use_case=CompleteEnergyBillDataUseCase(),
        estimate_solar_project_from_bill_use_case=estimate_from_bill,
        create_financing_simulation_use_case=CreateFinancingSimulationUseCase(
            LocalFinancingEngine(), repository
        ),
        check_simulation_status_use_case=CheckSimulationStatusUseCase(repository),
        monthly_rate=app_settings.monthly_rate,
        ocr_provider_name=app_settings.ocr_provider,
        closeables=[address_gateway, solar_gateway],
    )
