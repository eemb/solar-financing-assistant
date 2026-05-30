"""Integration tests simulating real user journeys through the CLI."""

import io
import re
from contextlib import redirect_stdout
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

import pytest

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
from solar_financing_assistant.infrastructure.financing.local_financing_engine import (
    LocalFinancingEngine,
)
from solar_financing_assistant.infrastructure.ocr.mock_ocr_adapter import MockOCRAdapter
from solar_financing_assistant.infrastructure.repositories.in_memory_simulation_repository import (
    InMemorySimulationRepository,
)
from solar_financing_assistant.interface.cli.chat_cli import ChatCLI

# ---------------------------------------------------------------------------
# Fake use cases (no network)
# ---------------------------------------------------------------------------


class _OfflineValidateAddressUseCase:
    """Always raises so EstimateSolarProjectFromBillUseCase uses the fallback."""

    async def execute(self, zipcode: str) -> None:
        raise Exception("No network in integration tests")


class _NeverCalledSolarPotentialUseCase:
    def execute(self, latitude: float, longitude: float) -> None:
        raise AssertionError("Solar potential should not be called in integration tests")


# ---------------------------------------------------------------------------
# Partial OCR adapter (returns a DTO missing non-critical fields)
# ---------------------------------------------------------------------------


class _PartialMockOCRAdapter:
    """Returns a DTO with the three fields required by ExtractEnergyBillDataUseCase
    but leaves customer_name, cpf, zipcode, tariff_brl_per_kwh, and
    reference_month absent to trigger the manual-completion flow."""

    async def extract_energy_bill_data(self, file_path: Path) -> ExtractedEnergyBillDataDTO:
        if not file_path.exists():
            raise FileNotFoundError(f"Energy bill file not found: {file_path}")
        return ExtractedEnergyBillDataDTO(
            monthly_consumption_kwh=450.0,
            monthly_cost_brl=Decimal("380.50"),
            distributor="Neoenergia Pernambuco",
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_cli(ocr_adapter=None) -> tuple[ChatCLI, InMemorySimulationRepository]:  # type: ignore[assignment]
    repository = InMemorySimulationRepository()
    adapter = ocr_adapter or MockOCRAdapter()

    estimate_solar_project_from_bill = EstimateSolarProjectFromBillUseCase(
        validate_address_use_case=_OfflineValidateAddressUseCase(),  # type: ignore[arg-type]
        get_solar_potential_use_case=_NeverCalledSolarPotentialUseCase(),  # type: ignore[arg-type]
        estimate_solar_project_use_case=EstimateSolarProjectUseCase(),
        fallback_generation_per_kwp_month=120.0,
        cost_per_kwp_brl=Decimal("5000.00"),
    )

    cli = ChatCLI(
        extract_energy_bill=ExtractEnergyBillDataUseCase(adapter),
        create_simulation=CreateFinancingSimulationUseCase(LocalFinancingEngine(), repository),
        check_status=CheckSimulationStatusUseCase(repository),
        estimate_solar_project_from_bill=estimate_solar_project_from_bill,
        monthly_rate=Decimal("0.019"),
        get_missing_energy_bill_fields_use_case=GetMissingEnergyBillFieldsUseCase(),
        complete_energy_bill_data_use_case=CompleteEnergyBillDataUseCase(),
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


@pytest.mark.integration
def test_user_fills_missing_fields_manually(bill_file: Path) -> None:
    """OCR returns partial DTO; user fills in the five absent fields manually."""
    cli, _ = _make_cli(_PartialMockOCRAdapter())

    # Missing fields in order: customer_name, cpf, zipcode,
    # tariff_brl_per_kwh, reference_month.
    out = _run(
        cli,
        [
            "1",
            str(bill_file),
            "Maria Souza",  # customer_name
            "529.982.247-25",  # cpf  (valid CPF)
            "52000-000",  # zipcode
            "0,8455",  # tariff_brl_per_kwh
            "2026-05",  # reference_month
            "s",  # confirm simulation
            "0",  # exit
        ],
    )

    assert "campos ausentes" in out
    assert "Dados extraídos da conta" in out
    assert "Maria Souza" in out
    assert "Resultado da simulação" in out
    assert "Status: approved" in out
