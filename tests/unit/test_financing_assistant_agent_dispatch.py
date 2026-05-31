"""Unit tests for FinancingAssistantAgent._execute_tool dispatch.

OpenAI is never called: only _execute_tool is exercised in isolation.
"""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import patch

import pytest

from solar_financing_assistant.infrastructure.llm.agent import FinancingAssistantAgent

# ---------------------------------------------------------------------------
# Minimal fake tools — only the methods exercised by _execute_tool
# ---------------------------------------------------------------------------


class _FakeTools:
    """Duck-typed stub that satisfies FinancingAssistantAgent's expectations."""

    async def extract_energy_bill_data(self, file_path: str) -> dict:
        return {"data": {"file_path": file_path}, "missing_fields": []}

    def complete_energy_bill_data(self, extracted_bill_data: dict, manual_values: dict) -> dict:
        merged = {**extracted_bill_data, **manual_values}
        return {"data": merged, "missing_fields": []}

    async def simulate_financing_from_bill(self, extracted_bill_data: dict) -> dict:
        return {"status": "approved", "simulation_id": "fake-uuid", "offer": {}}

    def check_simulation_status(self, simulation_id: str) -> dict:
        return {"simulation_id": simulation_id, "status": "approved"}

    # FinancingAssistantTools attributes accessed by __main__._run_cli
    monthly_rate: Decimal = Decimal("0.019")


# ---------------------------------------------------------------------------
# Fixture — agent created without touching OpenAI network
# ---------------------------------------------------------------------------


@pytest.fixture()
def agent() -> FinancingAssistantAgent:
    """Return an agent whose AsyncOpenAI client is never used."""
    with patch(
        "solar_financing_assistant.infrastructure.llm.agent.AsyncOpenAI",
        autospec=True,
    ):
        return FinancingAssistantAgent(
            tools=_FakeTools(),  # type: ignore[arg-type]
            api_key="test-key",
            model="gpt-4o-mini",
        )


# ---------------------------------------------------------------------------
# Unknown tool
# ---------------------------------------------------------------------------


async def test_execute_unknown_tool_returns_error(agent: FinancingAssistantAgent) -> None:
    result = await agent._execute_tool("nonexistent_tool", {})

    assert result["status"] == "error"
    assert "nonexistent_tool" in result["message"]


# ---------------------------------------------------------------------------
# check_simulation_status dispatch
# ---------------------------------------------------------------------------


async def test_dispatch_check_simulation_status(agent: FinancingAssistantAgent) -> None:
    result = await agent._execute_tool(
        "check_simulation_status",
        {"simulation_id": "abc-123"},
    )

    assert result["simulation_id"] == "abc-123"
    assert result["status"] == "approved"


# ---------------------------------------------------------------------------
# extract_energy_bill_data dispatch
# ---------------------------------------------------------------------------


async def test_dispatch_extract_energy_bill_data(agent: FinancingAssistantAgent) -> None:
    result = await agent._execute_tool(
        "extract_energy_bill_data",
        {"file_path": "/tmp/conta.pdf"},
    )

    assert "data" in result
    assert result["missing_fields"] == []


# ---------------------------------------------------------------------------
# complete_energy_bill_data dispatch
# ---------------------------------------------------------------------------


def test_dispatch_complete_energy_bill_data(agent: FinancingAssistantAgent) -> None:
    result = agent._tools.complete_energy_bill_data(  # type: ignore[attr-defined]
        {"distributor": "Cemig"},
        {"customer_name": "Ana"},
    )

    assert result["data"]["customer_name"] == "Ana"
    assert result["data"]["distributor"] == "Cemig"


# ---------------------------------------------------------------------------
# simulate_financing_from_bill dispatch
# ---------------------------------------------------------------------------


async def test_dispatch_simulate_financing_from_bill(agent: FinancingAssistantAgent) -> None:
    result = await agent._execute_tool(
        "simulate_financing_from_bill",
        {"extracted_bill_data": {"monthly_consumption_kwh": 450.0}},
    )

    assert result["status"] == "approved"
    assert "simulation_id" in result
