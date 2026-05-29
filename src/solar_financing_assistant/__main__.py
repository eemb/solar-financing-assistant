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
from solar_financing_assistant.application.use_cases.extract_energy_bill_data import (
    ExtractEnergyBillDataUseCase,
)
from solar_financing_assistant.config.settings import Settings, configure_logging
from solar_financing_assistant.infrastructure.financing.local_financing_engine import (
    LocalFinancingEngine,
)
from solar_financing_assistant.infrastructure.ocr.mock_ocr_adapter import MockOCRAdapter
from solar_financing_assistant.infrastructure.repositories.in_memory_simulation_repository import (
    InMemorySimulationRepository,
)
from solar_financing_assistant.interface.cli.chat_cli import ChatCLI


def main() -> None:
    configure_logging()
    app_settings = Settings()

    repository = InMemorySimulationRepository()
    extract_energy_bill = ExtractEnergyBillDataUseCase(MockOCRAdapter())
    create_simulation = CreateFinancingSimulationUseCase(
        LocalFinancingEngine(),
        repository,
    )
    check_status = CheckSimulationStatusUseCase(repository)
    estimate_solar_project = EstimateSolarProjectUseCase()

    ChatCLI(
        extract_energy_bill=extract_energy_bill,
        create_simulation=create_simulation,
        check_status=check_status,
        estimate_solar_project=estimate_solar_project,
        generation_per_kwp_month=app_settings.generation_per_kwp_month,
        cost_per_kwp_brl=app_settings.cost_per_kwp_brl,
        monthly_rate=app_settings.monthly_rate,
    ).run()


if __name__ == "__main__":
    main()
