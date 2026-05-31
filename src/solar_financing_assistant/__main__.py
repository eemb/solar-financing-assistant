"""Entry point for `python -m solar_financing_assistant`."""

from solar_financing_assistant.application.ports.use_case_ports import (
    CheckSimulationStatusPort,
    CompleteEnergyBillDataPort,
    CreateFinancingSimulationPort,
    EstimateSolarProjectFromBillPort,
    ExtractEnergyBillDataPort,
    GetMissingEnergyBillFieldsPort,
)
from solar_financing_assistant.bootstrap import build_tools
from solar_financing_assistant.config.settings import Settings, configure_logging
from solar_financing_assistant.interface.cli.chat_cli import ChatCLI


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

    tools = build_tools(app_settings)
    agent = FinancingAssistantAgent(
        tools=tools,
        api_key=api_key,
        model=app_settings.openai_model,
    )
    AgentCLI(agent).run()


def _run_cli(app_settings: Settings) -> None:
    tools = build_tools(app_settings)

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
