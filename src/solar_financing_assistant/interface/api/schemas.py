"""Pydantic schemas for the FastAPI interface."""

from __future__ import annotations

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    app_mode: str


class ExtractEnergyBillRequest(BaseModel):
    file_path: str


class ExtractEnergyBillResponse(BaseModel):
    data: dict
    missing_fields: list[str]


class CompleteEnergyBillRequest(BaseModel):
    extracted_bill_data: dict
    manual_values: dict[str, str]


class SimulationRequest(BaseModel):
    extracted_bill_data: dict
    confirm: bool = False


class SimulationResponse(BaseModel):
    status: str
    simulation_id: str | None = None
    message: str | None = None
    missing_fields: list[str] | None = None
    solar_project: dict | None = None
    offer: dict | None = None


class AgentChatRequest(BaseModel):
    messages: list[dict]


class AgentChatResponse(BaseModel):
    message: str
    raw: dict | None = None
