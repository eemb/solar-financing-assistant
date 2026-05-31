"""API route definitions."""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request

from solar_financing_assistant.config.settings import Settings
from solar_financing_assistant.infrastructure.llm.tools import FinancingAssistantTools
from solar_financing_assistant.interface.api.dependencies import (
    get_agent,
    get_settings,
    get_tools,
)
from solar_financing_assistant.interface.api.schemas import (
    AgentChatRequest,
    AgentChatResponse,
    CompleteEnergyBillRequest,
    ExtractEnergyBillRequest,
    ExtractEnergyBillResponse,
    HealthResponse,
    SimulationRequest,
    SimulationResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


@router.get("/health", response_model=HealthResponse)
def health(settings: Settings = Depends(get_settings)) -> HealthResponse:  # noqa: B008
    return HealthResponse(status="ok", app_mode=settings.app_mode)


# ---------------------------------------------------------------------------
# Energy bills
# ---------------------------------------------------------------------------


@router.post("/energy-bills/extract", response_model=ExtractEnergyBillResponse)
async def extract_energy_bill(
    body: ExtractEnergyBillRequest,
    tools: FinancingAssistantTools = Depends(get_tools),  # noqa: B008
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> ExtractEnergyBillResponse:
    allowed = Path(settings.upload_dir).resolve()
    requested = Path(body.file_path).resolve()
    if not requested.is_relative_to(allowed):
        raise HTTPException(
            status_code=400,
            detail="file_path must be inside the configured upload directory.",
        )

    result = await tools.extract_energy_bill_data(body.file_path)

    if result.get("status") == "error":
        raise HTTPException(status_code=422, detail=result.get("message", "Extraction failed."))

    return ExtractEnergyBillResponse(
        data=result.get("data", {}),
        missing_fields=result.get("missing_fields", []),
    )


@router.post("/energy-bills/complete", response_model=ExtractEnergyBillResponse)
def complete_energy_bill(
    body: CompleteEnergyBillRequest,
    tools: FinancingAssistantTools = Depends(get_tools),  # noqa: B008
) -> ExtractEnergyBillResponse:
    result = tools.complete_energy_bill_data(
        extracted_bill_data=body.extracted_bill_data,
        manual_values=body.manual_values,
    )

    if result.get("status") == "error":
        raise HTTPException(status_code=422, detail=result.get("message", "Completion failed."))

    return ExtractEnergyBillResponse(
        data=result.get("data", {}),
        missing_fields=result.get("missing_fields", []),
    )


# ---------------------------------------------------------------------------
# Simulations
# ---------------------------------------------------------------------------


@router.post("/simulations", response_model=SimulationResponse)
async def create_simulation(
    body: SimulationRequest,
    tools: FinancingAssistantTools = Depends(get_tools),  # noqa: B008
) -> SimulationResponse:
    if not body.confirm:
        return SimulationResponse(
            status="confirmation_required",
            message=(
                "A criação da simulação exige confirmação explícita. "
                "Envie a requisição novamente com o campo 'confirm' igual a true."
            ),
        )

    result = await tools.simulate_financing_from_bill(body.extracted_bill_data.model_dump())

    if result.get("status") == "error":
        raise HTTPException(status_code=422, detail=result.get("message", "Simulation failed."))

    if result.get("status") == "missing_fields":
        return SimulationResponse(
            status="missing_fields",
            missing_fields=result.get("missing_fields"),
            message="Campos obrigatórios ausentes na conta de energia.",
        )

    return SimulationResponse(
        status=result.get("status", "unknown"),
        simulation_id=result.get("simulation_id"),
        message=result.get("message"),
        solar_project=result.get("solar_project"),
        offer=result.get("offer"),
    )


@router.get("/simulations/{simulation_id}", response_model=SimulationResponse)
def get_simulation(
    simulation_id: str,
    tools: FinancingAssistantTools = Depends(get_tools),  # noqa: B008
) -> SimulationResponse:
    result = tools.check_simulation_status(simulation_id)

    if result.get("status") == "error":
        raise HTTPException(
            status_code=404,
            detail=result.get("message", "Simulation not found."),
        )

    return SimulationResponse(
        status=result.get("status", "unknown"),
        simulation_id=result.get("simulation_id"),
        message=result.get("message"),
        solar_project=result.get("solar_project"),
        offer=result.get("offer"),
    )


# ---------------------------------------------------------------------------
# Agent chat
# ---------------------------------------------------------------------------


@router.post("/agent/chat", response_model=AgentChatResponse)
async def agent_chat(body: AgentChatRequest, request: Request) -> AgentChatResponse:
    try:
        agent = get_agent(request)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    try:
        response = await agent.run_turn([m.model_dump() for m in body.messages])
    except Exception as exc:
        logger.exception("Agent run_turn failed")
        raise HTTPException(status_code=500, detail="Erro interno no agente.") from exc

    return AgentChatResponse(
        message=response.get("content", ""),
        raw=response,
    )
