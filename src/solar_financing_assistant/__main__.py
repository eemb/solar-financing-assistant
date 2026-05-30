"""Entry point for `python -m solar_financing_assistant`."""

from solar_financing_assistant.application.use_cases.check_simulation_status import (
    CheckSimulationStatusUseCase,
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
from solar_financing_assistant.infrastructure.ocr.ocr_adapter_factory import create_ocr_adapter
from solar_financing_assistant.infrastructure.repositories.in_memory_simulation_repository import (
    InMemorySimulationRepository,
)
from solar_financing_assistant.interface.cli.chat_cli import ChatCLI


def main() -> None:
    configure_logging()
    app_settings = Settings()

    repository = InMemorySimulationRepository()
    ocr_adapter = create_ocr_adapter(app_settings.ocr_provider)
    extract_energy_bill = ExtractEnergyBillDataUseCase(ocr_adapter)
    create_simulation = CreateFinancingSimulationUseCase(
        LocalFinancingEngine(),
        repository,
    )
    check_status = CheckSimulationStatusUseCase(repository)

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

    estimate_solar_project_from_bill = EstimateSolarProjectFromBillUseCase(
        validate_address_use_case=validate_address,
        get_solar_potential_use_case=get_solar_potential,
        estimate_solar_project_use_case=estimate_solar_project,
        fallback_generation_per_kwp_month=app_settings.generation_per_kwp_month,
        cost_per_kwp_brl=app_settings.cost_per_kwp_brl,
    )

    ChatCLI(
        extract_energy_bill=extract_energy_bill,
        create_simulation=create_simulation,
        check_status=check_status,
        estimate_solar_project_from_bill=estimate_solar_project_from_bill,
        monthly_rate=app_settings.monthly_rate,
    ).run()


if __name__ == "__main__":
    main()
