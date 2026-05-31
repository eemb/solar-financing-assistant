"""FastAPI dependency providers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import Request

from solar_financing_assistant.config.settings import Settings
from solar_financing_assistant.infrastructure.llm.tools import FinancingAssistantTools
from solar_financing_assistant.interface.api.state import AppState

if TYPE_CHECKING:
    from solar_financing_assistant.infrastructure.llm.agent import FinancingAssistantAgent


def _app_state(request: Request) -> AppState:
    return request.app.state.app_state  # type: ignore[no-any-return]


def get_settings(request: Request) -> Settings:
    """Return the application-scoped Settings singleton."""
    return _app_state(request).settings


def get_tools(request: Request) -> FinancingAssistantTools:
    """Return the application-scoped FinancingAssistantTools singleton."""
    return _app_state(request).tools


def get_agent(request: Request) -> FinancingAssistantAgent:
    """Return the application-scoped FinancingAssistantAgent, or raise if not configured."""
    agent = _app_state(request).agent
    if agent is None:
        raise RuntimeError(
            "OPENAI_API_KEY não configurada. "
            "Defina a variável de ambiente para usar o endpoint /agent/chat."
        )
    return agent
