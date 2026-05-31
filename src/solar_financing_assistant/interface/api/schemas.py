"""Pydantic schemas for the FastAPI interface."""

from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, field_validator

from solar_financing_assistant.application.dtos.extracted_energy_bill_data_dto import (
    ExtractedEnergyBillDataDTO,
)


class HealthResponse(BaseModel):
    status: str
    app_mode: str


# ---------------------------------------------------------------------------
# Energy bills
# ---------------------------------------------------------------------------


class ExtractEnergyBillRequest(BaseModel):
    file_path: str

    @field_validator("file_path")
    @classmethod
    def validate_no_traversal(cls, v: str) -> str:
        if ".." in v:
            raise ValueError("file_path must not contain path traversal components.")
        return v


class ExtractEnergyBillResponse(BaseModel):
    data: ExtractedEnergyBillDataDTO
    missing_fields: list[str]


class CompleteEnergyBillRequest(BaseModel):
    extracted_bill_data: dict
    manual_values: dict[str, str]


# ---------------------------------------------------------------------------
# Simulations
# ---------------------------------------------------------------------------


class SolarProjectResponse(BaseModel):
    id: str | None = None
    monthly_consumption_kwh: float | None = None
    estimated_system_kwp: float | None = None
    estimated_monthly_generation_kwh: float | None = None
    estimated_project_cost: Decimal | None = None


class FinancingOfferResponse(BaseModel):
    id: str | None = None
    approved_amount: Decimal | None = None
    installment_amount: Decimal | None = None
    number_of_installments: int | None = None
    monthly_rate: Decimal | None = None
    total_cost: Decimal | None = None


class SimulationRequest(BaseModel):
    extracted_bill_data: dict
    confirm: bool = False


class SimulationResponse(BaseModel):
    status: str
    simulation_id: str | None = None
    message: str | None = None
    missing_fields: list[str] | None = None
    solar_project: SolarProjectResponse | None = None
    offer: FinancingOfferResponse | None = None


# ---------------------------------------------------------------------------
# Agent chat
# ---------------------------------------------------------------------------


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class AgentChatRequest(BaseModel):
    messages: list[ChatMessage]


class AgentChatResponse(BaseModel):
    message: str
    raw: dict | None = None
