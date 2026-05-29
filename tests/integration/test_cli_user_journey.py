"""Integration tests simulating real user journeys through the CLI."""

import io
import re
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import pytest

from solar_financing_assistant.application.use_cases.check_simulation_status import (
    CheckSimulationStatusUseCase,
)
from solar_financing_assistant.application.use_cases.create_financing_simulation import (
    CreateFinancingSimulationUseCase,
)
from solar_financing_assistant.application.use_cases.extract_energy_bill_data import (
    ExtractEnergyBillDataUseCase,
)
from solar_financing_assistant.infrastructure.financing.local_financing_engine import (
    LocalFinancingEngine,
)
from solar_financing_assistant.infrastructure.ocr.mock_ocr_adapter import MockOCRAdapter
from solar_financing_assistant.infrastructure.repositories.in_memory_simulation_repository import (
    InMemorySimulationRepository,
)
from solar_financing_assistant.interface.cli.chat_cli import ChatCLI

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_cli() -> tuple[ChatCLI, InMemorySimulationRepository]:
    repository = InMemorySimulationRepository()
    cli = ChatCLI(
        extract_energy_bill=ExtractEnergyBillDataUseCase(MockOCRAdapter()),
        create_simulation=CreateFinancingSimulationUseCase(LocalFinancingEngine(), repository),
        check_status=CheckSimulationStatusUseCase(repository),
    )
    return cli, repository


def _run(cli: ChatCLI, inputs: list[str]) -> str:
    buf = io.StringIO()
    with redirect_stdout(buf), patch("builtins.input", side_effect=inputs):
        cli.run()
    return buf.getvalue()


@pytest.fixture()
def bill_file(tmp_path: Path) -> Path:
    path = tmp_path / "conta.pdf"
    path.write_bytes(b"%PDF-1.4 fake content")
    return path


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_user_exits_immediately() -> None:
    cli, _ = _make_cli()

    out = _run(cli, ["0"])

    assert "Até logo!" in out


@pytest.mark.integration
def test_user_simulates_financing_full_journey(bill_file: Path) -> None:
    cli, _ = _make_cli()

    out = _run(cli, ["1", str(bill_file), "s", "0"])

    assert "Dados extraídos da conta" in out
    assert "João da Silva" in out
    assert "Neoenergia Pernambuco" in out
    assert "Projeto solar estimado" in out
    assert "Resultado da simulação" in out
    assert "SIM-" in out
    assert "Parcela (R$):" in out
    assert "Status: approved" in out


@pytest.mark.integration
def test_user_cancels_simulation(bill_file: Path) -> None:
    cli, _ = _make_cli()

    out = _run(cli, ["1", str(bill_file), "n", "0"])

    assert "Simulação cancelada." in out
    assert "Resultado da simulação" not in out


@pytest.mark.integration
def test_user_checks_status_of_existing_simulation(bill_file: Path) -> None:
    cli, _ = _make_cli()

    # First session: create a simulation and capture the UUID printed to stdout.
    out1 = _run(cli, ["1", str(bill_file), "s", "0"])
    match = re.search(r"ID para consulta: ([0-9a-f-]{36})", out1)
    assert match is not None, f"UUID not found in output:\n{out1}"
    sim_uuid = match.group(1)

    # Second session (same repository): check status using the captured UUID.
    out2 = _run(cli, ["2", sim_uuid, "0"])

    assert "Status: approved" in out2
    assert "Parcela (R$):" in out2


@pytest.mark.integration
def test_user_consults_status_with_unknown_id() -> None:
    from uuid import uuid4

    cli, _ = _make_cli()

    out = _run(cli, ["2", str(uuid4()), "0"])

    assert "Simulation not found" in out


@pytest.mark.integration
def test_user_enters_invalid_menu_option() -> None:
    cli, _ = _make_cli()

    out = _run(cli, ["9", "0"])

    assert "Opção inválida" in out


@pytest.mark.integration
def test_user_provides_empty_file_path() -> None:
    cli, _ = _make_cli()

    out = _run(cli, ["1", "", "0"])

    assert "Caminho não informado" in out


@pytest.mark.integration
def test_user_provides_invalid_uuid_for_status() -> None:
    cli, _ = _make_cli()

    out = _run(cli, ["2", "nao-e-um-uuid", "0"])

    assert "UUID" in out or "inválido" in out
