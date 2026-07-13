"""Unit tests for FinancingAssistantTools.

Uses real use case implementations with:
  - MockOCRAdapter       (offline — no Tesseract required)
  - InMemorySimulationRepository
  - LocalFinancingEngine
  - Fake offline stubs for address / solar-potential gateways
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from solar_financing_assistant.application.dtos.extracted_energy_bill_data_dto import (
    ExtractedEnergyBillDataDTO,
)
from solar_financing_assistant.application.dtos.solar_potential_dto import SolarPotentialDTO
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
from solar_financing_assistant.domain.entities.address import Address
from solar_financing_assistant.infrastructure.financing.local_financing_engine import (
    LocalFinancingEngine,
)
from solar_financing_assistant.infrastructure.llm.tools import FinancingAssistantTools
from solar_financing_assistant.infrastructure.ocr.mock_ocr_adapter import MockOCRAdapter
from solar_financing_assistant.infrastructure.repositories.in_memory_simulation_repository import (
    InMemorySimulationRepository,
)

# ---------------------------------------------------------------------------
# Offline fakes for network-dependent use cases
# ---------------------------------------------------------------------------

_FAKE_ADDRESS = Address(
    zip_code="52000000",
    street="Rua Exemplo",
    number=None,
    neighborhood="Bairro",
    city="Recife",
    state="PE",
    latitude=None,
    longitude=None,
)

_FAKE_SOLAR_POTENTIAL = SolarPotentialDTO(
    latitude=-8.0476,
    longitude=-34.877,
    estimated_daily_generation_kwh_per_kwp=4.0,
)


class _FakeValidateAddress:
    async def execute(self, zipcode: str) -> Address:
        return _FAKE_ADDRESS


class _FakeGetSolarPotential:
    async def execute(self, latitude: float, longitude: float) -> SolarPotentialDTO:
        return _FAKE_SOLAR_POTENTIAL


# ---------------------------------------------------------------------------
# Shared fixture factory
# ---------------------------------------------------------------------------

_MONTHLY_RATE = Decimal("0.019")
_FALLBACK_GEN = 120.0
_COST_PER_KWP = Decimal("5000.00")


def _make_tools() -> FinancingAssistantTools:
    repository = InMemorySimulationRepository()

    extract_uc = ExtractEnergyBillDataUseCase(MockOCRAdapter())
    get_missing_uc = GetMissingEnergyBillFieldsUseCase()
    complete_uc = CompleteEnergyBillDataUseCase()
    estimate_uc = EstimateSolarProjectFromBillUseCase(
        validate_address_use_case=_FakeValidateAddress(),
        get_solar_potential_use_case=_FakeGetSolarPotential(),
        estimate_solar_project_use_case=EstimateSolarProjectUseCase(),
        fallback_generation_per_kwp_month=_FALLBACK_GEN,
        cost_per_kwp_brl=_COST_PER_KWP,
    )
    create_uc = CreateFinancingSimulationUseCase(LocalFinancingEngine(), repository)
    check_uc = CheckSimulationStatusUseCase(repository)

    return FinancingAssistantTools(
        extract_energy_bill_data_use_case=extract_uc,
        get_missing_energy_bill_fields_use_case=get_missing_uc,
        complete_energy_bill_data_use_case=complete_uc,
        estimate_solar_project_from_bill_use_case=estimate_uc,
        create_financing_simulation_use_case=create_uc,
        check_simulation_status_use_case=check_uc,
        monthly_rate=_MONTHLY_RATE,
    )


# ---------------------------------------------------------------------------
# Helper: a complete bill dict (mirrors MockOCRAdapter output)
# ---------------------------------------------------------------------------


def _complete_bill_dict() -> dict:
    return ExtractedEnergyBillDataDTO(
        customer_name="João da Silva",
        cpf="12345678909",
        zipcode="52000000",
        distributor="Neoenergia Pernambuco",
        monthly_consumption_kwh=450.0,
        monthly_cost_brl=Decimal("380.50"),
        tariff_brl_per_kwh=Decimal("0.8455"),
        reference_month="2026-05",
    ).model_dump(mode="json")


# ---------------------------------------------------------------------------
# Tests — extract_energy_bill_data
# ---------------------------------------------------------------------------


async def test_extract_energy_bill_data_returns_data_and_missing_fields(
    tmp_path: Path,
) -> None:
    """MockOCRAdapter returns a fully filled DTO; missing_fields must be empty."""
    bill_file = tmp_path / "bill.png"
    bill_file.write_bytes(b"fake")

    tools = _make_tools()
    result = await tools.extract_energy_bill_data(str(bill_file))

    assert "data" in result
    assert "missing_fields" in result
    assert result["missing_fields"] == []
    assert result["data"]["distributor"] == "Neoenergia Pernambuco"
    assert result["data"]["monthly_consumption_kwh"] == 450.0


async def test_extract_energy_bill_data_returns_error_for_nonexistent_file() -> None:
    tools = _make_tools()
    result = await tools.extract_energy_bill_data("/nonexistent/file.png")

    assert result["status"] == "error"
    assert "message" in result


# ---------------------------------------------------------------------------
# Tests — complete_energy_bill_data
# ---------------------------------------------------------------------------


def test_complete_energy_bill_data_fills_missing_fields() -> None:
    """Fields absent in the DTO must be populated from manual_values."""
    partial = ExtractedEnergyBillDataDTO(
        monthly_consumption_kwh=300.0,
        monthly_cost_brl=Decimal("250.00"),
        distributor="Cemig",
    ).model_dump(mode="json")

    tools = _make_tools()
    result = tools.complete_energy_bill_data(
        partial,
        manual_values={
            "customer_name": "Maria Souza",
            "cpf": "52998224725",
            "zipcode": "30130010",
            "tariff_brl_per_kwh": "0,8000",
            "reference_month": "2026-04",
        },
    )

    assert result["data"]["customer_name"] == "Maria Souza"
    assert result["data"]["zipcode"] == "30130010"
    assert result["missing_fields"] == []


def test_complete_energy_bill_data_does_not_overwrite_existing_fields() -> None:
    """OCR-extracted fields must not be replaced by manual values."""
    bill_dict = _complete_bill_dict()

    tools = _make_tools()
    result = tools.complete_energy_bill_data(
        bill_dict,
        manual_values={"distributor": "Outra Distribuidora"},
    )

    assert result["data"]["distributor"] == "Neoenergia Pernambuco"


# ---------------------------------------------------------------------------
# Tests — simulate_financing_from_bill
# ---------------------------------------------------------------------------


async def test_simulate_financing_returns_missing_fields_when_dto_incomplete() -> None:
    """A DTO with absent required fields must short-circuit with status='missing_fields'."""
    incomplete = ExtractedEnergyBillDataDTO(
        monthly_consumption_kwh=400.0,
    ).model_dump(mode="json")

    tools = _make_tools()
    result = await tools.simulate_financing_from_bill(incomplete)

    assert result["status"] == "missing_fields"
    assert "missing_fields" in result
    assert len(result["missing_fields"]) > 0


async def test_simulate_financing_creates_simulation_when_dto_complete() -> None:
    """A fully populated DTO must produce an approved simulation."""
    tools = _make_tools()
    result = await tools.simulate_financing_from_bill(_complete_bill_dict())

    assert result["status"] == "approved"
    assert "simulation_id" in result
    assert "access_token" in result
    assert result["solar_project"] is not None
    assert result["offer"] is not None
    assert result["offer"]["number_of_installments"] == 60


async def test_simulate_financing_result_is_json_serialisable() -> None:
    """All dict values must survive a round-trip through json.dumps/loads."""
    import json

    tools = _make_tools()
    result = await tools.simulate_financing_from_bill(_complete_bill_dict())

    serialised = json.dumps(result)
    recovered = json.loads(serialised)
    assert recovered["status"] == "approved"


# ---------------------------------------------------------------------------
# Tests — check_simulation_status
# ---------------------------------------------------------------------------


async def test_check_simulation_status_returns_existing_simulation() -> None:
    """After simulate_financing_from_bill, check_simulation_status must find it."""
    tools = _make_tools()
    sim_result = await tools.simulate_financing_from_bill(_complete_bill_dict())

    sim_id = sim_result["simulation_id"]
    access_token = sim_result["access_token"]
    status_result = tools.check_simulation_status(sim_id, access_token=access_token)

    assert status_result["simulation_id"] == sim_id
    assert status_result["status"] == "approved"
    assert status_result["offer"] is not None


async def test_check_simulation_status_rejects_wrong_token() -> None:
    """check_simulation_status must return error when the access token is wrong."""
    tools = _make_tools()
    sim_result = await tools.simulate_financing_from_bill(_complete_bill_dict())

    sim_id = sim_result["simulation_id"]
    result = tools.check_simulation_status(sim_id, access_token="wrong-token")

    assert result["status"] == "error"
    assert "token" in result["message"].lower()


def test_check_simulation_status_returns_error_for_unknown_id() -> None:
    """A UUID not in the repository must return status='error'."""
    tools = _make_tools()
    result = tools.check_simulation_status("00000000-0000-0000-0000-000000000000")

    assert result["status"] == "error"
    assert "message" in result


def test_check_simulation_status_returns_error_for_invalid_uuid() -> None:
    """A non-UUID string must return status='error' without raising."""
    tools = _make_tools()
    result = tools.check_simulation_status("not-a-uuid")

    assert result["status"] == "error"
    assert "Invalid simulation ID" in result["message"]


# ---------------------------------------------------------------------------
# Tests — aclose releases registered resources (no httpx client leak)
# ---------------------------------------------------------------------------


async def test_aclose_releases_registered_closeables() -> None:
    """aclose must close every registered resource exactly once and be idempotent."""

    class _FakeClient:
        def __init__(self) -> None:
            self.closed = 0

        async def aclose(self) -> None:
            self.closed += 1

    client_a, client_b = _FakeClient(), _FakeClient()

    repository = InMemorySimulationRepository()
    tools = FinancingAssistantTools(
        extract_energy_bill_data_use_case=ExtractEnergyBillDataUseCase(MockOCRAdapter()),
        get_missing_energy_bill_fields_use_case=GetMissingEnergyBillFieldsUseCase(),
        complete_energy_bill_data_use_case=CompleteEnergyBillDataUseCase(),
        estimate_solar_project_from_bill_use_case=EstimateSolarProjectFromBillUseCase(
            validate_address_use_case=_FakeValidateAddress(),
            get_solar_potential_use_case=_FakeGetSolarPotential(),
            estimate_solar_project_use_case=EstimateSolarProjectUseCase(),
            fallback_generation_per_kwp_month=_FALLBACK_GEN,
            cost_per_kwp_brl=_COST_PER_KWP,
        ),
        create_financing_simulation_use_case=CreateFinancingSimulationUseCase(
            LocalFinancingEngine(), repository
        ),
        check_simulation_status_use_case=CheckSimulationStatusUseCase(repository),
        monthly_rate=_MONTHLY_RATE,
        closeables=[client_a, client_b],
    )

    await tools.aclose()
    await tools.aclose()  # idempotent — must not close twice or raise

    assert client_a.closed == 1
    assert client_b.closed == 1
