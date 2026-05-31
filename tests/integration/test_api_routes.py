"""Integration tests for the FastAPI HTTP interface.

All tests run fully offline:
- No OpenAI calls (get_agent is mocked or raises RuntimeError)
- No external HTTP calls (tools methods are mocked)
- No real OCR (get_tools is overridden with a mock)
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from solar_financing_assistant.config.settings import Settings
from solar_financing_assistant.interface.api.app import create_app
from solar_financing_assistant.interface.api.dependencies import get_settings, get_tools

# ---------------------------------------------------------------------------
# Shared fake data
# ---------------------------------------------------------------------------

_FAKE_BILL_DATA: dict[str, Any] = {
    "customer_name": "João da Silva",
    "cpf": "12345678909",
    "zipcode": "52000000",
    "distributor": "Neoenergia Pernambuco",
    "monthly_consumption_kwh": 450.0,
    "monthly_cost_brl": "380.50",
    "tariff_brl_per_kwh": "0.8455",
    "reference_month": "2026-05",
}

_FAKE_SIMULATION_RESULT: dict[str, Any] = {
    "simulation_id": "11111111-1111-1111-1111-111111111111",
    "status": "approved",
    "message": "Simulação aprovada com oferta de financiamento.",
    "solar_potential_source": "fallback",
    "solar_potential_fallback_warning": None,
    "solar_project": {
        "id": "22222222-2222-2222-2222-222222222222",
        "monthly_consumption_kwh": 450.0,
        "estimated_system_kwp": 3.75,
        "estimated_monthly_generation_kwh": 450.0,
        "estimated_project_cost": "18750.00",
    },
    "offer": {
        "id": "33333333-3333-3333-3333-333333333333",
        "approved_amount": "18750.00",
        "installment_amount": "468.10",
        "number_of_installments": 60,
        "monthly_rate": "0.019",
        "total_cost": "28086.00",
    },
}

# All integration test file paths must live under this directory so the
# allowlist check in the extract endpoint passes.  Using gettempdir() keeps
# paths cross-platform (Linux /tmp, Windows %TEMP%).
_UPLOAD_DIR = tempfile.gettempdir()
_UPLOAD_BILL = str(Path(_UPLOAD_DIR) / "bill.pdf")
_UPLOAD_BAD = str(Path(_UPLOAD_DIR) / "bad" / "path")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_mock_tools() -> MagicMock:
    """Return a MagicMock that mimics FinancingAssistantTools."""
    mock = MagicMock()

    mock.extract_energy_bill_data = AsyncMock(
        return_value={
            "data": _FAKE_BILL_DATA,
            "missing_fields": [],
            "data_source": "mock",
        }
    )
    mock.complete_energy_bill_data = MagicMock(
        return_value={
            "data": _FAKE_BILL_DATA,
            "missing_fields": [],
        }
    )
    mock.simulate_financing_from_bill = AsyncMock(return_value=_FAKE_SIMULATION_RESULT)
    mock.check_simulation_status = MagicMock(return_value=_FAKE_SIMULATION_RESULT)
    return mock


@pytest.fixture()
def client() -> TestClient:
    """TestClient with get_tools and get_settings overridden by mocks."""
    application = create_app()
    mock_tools = _make_mock_tools()
    mock_settings = Settings(upload_dir=_UPLOAD_DIR)
    application.dependency_overrides[get_tools] = lambda: mock_tools
    application.dependency_overrides[get_settings] = lambda: mock_settings
    return TestClient(application)


@pytest.fixture()
def mock_tools(client: TestClient) -> MagicMock:
    """Return the mock tools injected into the client's app."""
    return client.app.dependency_overrides[get_tools]()  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# GET /health
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_health_returns_200(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "app_mode" in body


# ---------------------------------------------------------------------------
# POST /energy-bills/extract
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_extract_energy_bill_returns_data_and_missing_fields(client: TestClient) -> None:
    response = client.post("/energy-bills/extract", json={"file_path": _UPLOAD_BILL})

    assert response.status_code == 200
    body = response.json()
    assert "data" in body
    assert "missing_fields" in body
    assert body["data"]["customer_name"] == "João da Silva"
    assert body["missing_fields"] == []


@pytest.mark.integration
def test_extract_energy_bill_error_returns_422(client: TestClient) -> None:
    mock_tools = client.app.dependency_overrides[get_tools]()  # type: ignore[attr-defined]
    mock_tools.extract_energy_bill_data = AsyncMock(
        return_value={"status": "error", "message": f"Arquivo não encontrado: {_UPLOAD_BAD}"}
    )

    response = client.post("/energy-bills/extract", json={"file_path": _UPLOAD_BAD})

    assert response.status_code == 422
    assert "Arquivo não encontrado" in response.json()["detail"]


@pytest.mark.integration
def test_extract_energy_bill_rejects_path_outside_upload_dir(client: TestClient) -> None:
    response = client.post("/energy-bills/extract", json={"file_path": "/etc/passwd"})

    assert response.status_code == 400
    assert "upload directory" in response.json()["detail"]


@pytest.mark.integration
def test_extract_energy_bill_rejects_path_traversal(client: TestClient) -> None:
    traversal = str(Path(_UPLOAD_DIR) / ".." / "etc" / "passwd")
    response = client.post("/energy-bills/extract", json={"file_path": traversal})

    # The schema validator catches ".." before the request reaches the route.
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# POST /energy-bills/complete
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_complete_energy_bill_merges_manual_values(client: TestClient) -> None:
    body = {
        "extracted_bill_data": {**_FAKE_BILL_DATA, "customer_name": None},
        "manual_values": {"customer_name": "Maria Silva"},
    }

    response = client.post("/energy-bills/complete", json=body)

    assert response.status_code == 200
    result = response.json()
    assert "data" in result
    assert "missing_fields" in result


# ---------------------------------------------------------------------------
# POST /simulations — confirm=false
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_simulation_without_confirm_returns_confirmation_required(client: TestClient) -> None:
    response = client.post(
        "/simulations",
        json={"extracted_bill_data": _FAKE_BILL_DATA, "confirm": False},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "confirmation_required"
    assert body["message"] is not None
    assert "confirm" in body["message"].lower() or "confirmação" in body["message"].lower()


# ---------------------------------------------------------------------------
# POST /simulations — confirm=true
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_simulation_with_confirm_creates_simulation(client: TestClient) -> None:
    response = client.post(
        "/simulations",
        json={"extracted_bill_data": _FAKE_BILL_DATA, "confirm": True},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "approved"
    assert body["simulation_id"] == "11111111-1111-1111-1111-111111111111"
    assert body["offer"] is not None
    assert body["solar_project"] is not None


@pytest.mark.integration
def test_simulation_with_missing_fields_returns_missing_fields_status(
    client: TestClient,
) -> None:
    mock_tools = client.app.dependency_overrides[get_tools]()  # type: ignore[attr-defined]
    mock_tools.simulate_financing_from_bill = AsyncMock(
        return_value={"status": "missing_fields", "missing_fields": ["zipcode", "cpf"]}
    )

    response = client.post(
        "/simulations",
        json={"extracted_bill_data": {}, "confirm": True},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "missing_fields"
    assert "zipcode" in body["missing_fields"]


# ---------------------------------------------------------------------------
# GET /simulations/{simulation_id}
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_get_simulation_returns_existing_simulation(client: TestClient) -> None:
    sim_id = "11111111-1111-1111-1111-111111111111"

    response = client.get(f"/simulations/{sim_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "approved"
    assert body["simulation_id"] == sim_id


@pytest.mark.integration
def test_get_simulation_with_invalid_id_returns_404(client: TestClient) -> None:
    mock_tools = client.app.dependency_overrides[get_tools]()  # type: ignore[attr-defined]
    mock_tools.check_simulation_status = MagicMock(
        return_value={"status": "error", "message": "Invalid simulation ID: 'not-a-uuid'"}
    )

    response = client.get("/simulations/not-a-uuid")

    assert response.status_code == 404
    assert "not-a-uuid" in response.json()["detail"] or response.json()["detail"]


# ---------------------------------------------------------------------------
# POST /agent/chat
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_agent_chat_without_openai_key_returns_503(client: TestClient) -> None:
    """When OPENAI_API_KEY is absent, /agent/chat must return 503 without calling OpenAI."""
    with patch(
        "solar_financing_assistant.interface.api.routes.get_agent",
        side_effect=RuntimeError("OPENAI_API_KEY não configurada."),
    ):
        response = client.post(
            "/agent/chat",
            json={"messages": [{"role": "user", "content": "Olá"}]},
        )

    assert response.status_code == 503
    assert "OPENAI_API_KEY" in response.json()["detail"]


@pytest.mark.integration
def test_agent_chat_with_valid_key_returns_message(client: TestClient) -> None:
    """Agent chat returns the assistant message when the agent is properly configured."""
    fake_agent = MagicMock()
    fake_agent.run_turn = AsyncMock(
        return_value={"role": "assistant", "content": "Olá! Como posso ajudar?"}
    )

    with patch(
        "solar_financing_assistant.interface.api.routes.get_agent",
        return_value=fake_agent,
    ):
        response = client.post(
            "/agent/chat",
            json={"messages": [{"role": "user", "content": "Olá"}]},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["message"] == "Olá! Como posso ajudar?"
