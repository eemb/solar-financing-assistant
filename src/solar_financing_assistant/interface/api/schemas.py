"""Pydantic schemas for the FastAPI interface."""

from __future__ import annotations

from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, Field, field_validator

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


class ExtractedBillPublic(BaseModel):
    """Public-facing energy-bill data with the CPF partially masked."""

    customer_name: str | None = None
    cpf: str | None = None
    zipcode: str | None = None
    distributor: str | None = None
    monthly_consumption_kwh: float | None = None
    monthly_cost_brl: Decimal | None = None
    tariff_brl_per_kwh: Decimal | None = None
    reference_month: str | None = None

    @classmethod
    def from_dto(cls, dto: ExtractedEnergyBillDataDTO) -> ExtractedBillPublic:
        masked_cpf = f"{dto.cpf[:3]}.***.***.{dto.cpf[-2:]}" if dto.cpf else None
        return cls(**dto.model_dump(exclude={"cpf"}), cpf=masked_cpf)


class ExtractEnergyBillResponse(BaseModel):
    data: ExtractedBillPublic
    missing_fields: list[str]


class CompleteEnergyBillRequest(BaseModel):
    extracted_bill_data: ExtractedEnergyBillDataDTO
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
    extracted_bill_data: ExtractedEnergyBillDataDTO
    confirm: bool = False


class SimulationResponse(BaseModel):
    status: str
    simulation_id: str | None = None
    message: str | None = None
    missing_fields: list[str] | None = None
    solar_project: SolarProjectResponse | None = None
    offer: FinancingOfferResponse | None = None
    access_token: str | None = None


# ---------------------------------------------------------------------------
# Agent chat
# ---------------------------------------------------------------------------

BoundedContent = Annotated[str, Field(min_length=1, max_length=4_000)]


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: BoundedContent


class AgentChatRequest(BaseModel):
    messages: Annotated[list[ChatMessage], Field(min_length=1, max_length=50)]


class AgentChatResponse(BaseModel):
    message: str
