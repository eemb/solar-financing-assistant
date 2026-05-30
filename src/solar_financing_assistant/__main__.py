"""Entry point for `python -m solar_financing_assistant`."""

from solar_financing_assistant.application.ports.use_case_ports import (
    CheckSimulationStatusPort,
    CompleteEnergyBillDataPort,
    CreateFinancingSimulationPort,
    EstimateSolarProjectFromBillPort,
    ExtractEnergyBillDataPort,
    GetMissingEnergyBillFieldsPort,
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
from solar_financing_assistant.config.settings import Settings, configure_logging
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
from solar_financing_assistant.interface.cli.chat_cli import ChatCLI


def _build_tools(app_settings: Settings) -> FinancingAssistantTools:
    """Construct FinancingAssistantTools with all required use cases."""
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
    )


def main() -> None:
    configure_logging()
    app_settings = Settings()

    if app_settings.app_mode == "agent":
        _run_agent(app_settings)
    else:
        _run_cli(app_settings)


def _run_agent(app_settings: Settings) -> None:
    from solar_financing_assistant.infrastructure.llm.agent import FinancingAssistantAgent
    from solar_financing_assistant.interface.cli.agent_cli import AgentCLI

    api_key = app_settings.openai_api_key
    if not api_key or api_key == "sk-your-key-here":
        print(
            "Erro: OPENAI_API_KEY não configurada.\n"
            "Configure a variável no arquivo .env para usar o modo agente.\n"
            "Exemplo: OPENAI_API_KEY=sk-..."
        )
        return

    tools = _build_tools(app_settings)
    agent = FinancingAssistantAgent(
        tools=tools,
        api_key=api_key,
        model=app_settings.openai_model,
    )
    AgentCLI(agent).run()


def _run_cli(app_settings: Settings) -> None:
    tools = _build_tools(app_settings)

    extract_energy_bill: ExtractEnergyBillDataPort = tools._extract_bill
    create_simulation: CreateFinancingSimulationPort = tools._create_simulation
    check_status: CheckSimulationStatusPort = tools._check_status
    estimate_solar_project_from_bill: EstimateSolarProjectFromBillPort = tools._estimate_project
    get_missing_fields: GetMissingEnergyBillFieldsPort = tools._get_missing
    complete_bill_data: CompleteEnergyBillDataPort = tools._complete_bill

    ChatCLI(
        extract_energy_bill=extract_energy_bill,
        create_simulation=create_simulation,
        check_status=check_status,
        estimate_solar_project_from_bill=estimate_solar_project_from_bill,
        monthly_rate=app_settings.monthly_rate,
        get_missing_energy_bill_fields_use_case=get_missing_fields,
        complete_energy_bill_data_use_case=complete_bill_data,
    ).run()


if __name__ == "__main__":
    main()
