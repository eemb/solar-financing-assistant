"""FastAPI dependency providers.

All application-scoped singletons (Settings, FinancingAssistantTools,
FinancingAssistantAgent) are created once during the lifespan event in app.py
and stored on ``app.state``.  These dependency functions simply retrieve them
from the request context — no global state, no lru_cache, no cross-test
leakage.
"""

from __future__ import annotations

from fastapi import Request

from solar_financing_assistant.config.settings import Settings
from solar_financing_assistant.infrastructure.llm.tools import FinancingAssistantTools


def get_settings(request: Request) -> Settings:
    """Return the application-scoped Settings singleton."""
    return request.app.state.settings  # type: ignore[no-any-return]


def get_tools(request: Request) -> FinancingAssistantTools:
    """Return the application-scoped FinancingAssistantTools singleton."""
    return request.app.state.tools  # type: ignore[no-any-return]


def get_agent(request: Request):  # noqa: ANN201
    """Return the application-scoped FinancingAssistantAgent, or raise if not configured."""
    agent = request.app.state.agent
    if agent is None:
        raise RuntimeError(
            "OPENAI_API_KEY não configurada. "
            "Defina a variável de ambiente para usar o endpoint /agent/chat."
        )
    return agent
