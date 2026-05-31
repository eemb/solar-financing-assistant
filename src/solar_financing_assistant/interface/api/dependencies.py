"""FastAPI dependency providers.

The tools singleton is built once at module import time so that the
InMemorySimulationRepository is shared across all requests within a single
server process.  get_agent() is intentionally lazy and raises a clear error
when OPENAI_API_KEY is absent.
"""

from __future__ import annotations

from functools import lru_cache

from solar_financing_assistant.bootstrap import build_tools
from solar_financing_assistant.config.settings import Settings
from solar_financing_assistant.infrastructure.llm.tools import FinancingAssistantTools


@lru_cache(maxsize=1)
def _cached_settings() -> Settings:
    return Settings()


@lru_cache(maxsize=1)
def _cached_tools() -> FinancingAssistantTools:
    return build_tools(_cached_settings())


def get_tools() -> FinancingAssistantTools:
    """Return the application-scoped FinancingAssistantTools singleton."""
    return _cached_tools()


def get_agent():  # noqa: ANN201
    """Return a FinancingAssistantAgent, or raise RuntimeError if not configured."""
    from solar_financing_assistant.infrastructure.llm.agent import FinancingAssistantAgent

    settings = _cached_settings()
    api_key = settings.openai_api_key

    if not api_key or api_key == "sk-your-key-here":
        raise RuntimeError(
            "OPENAI_API_KEY não configurada. "
            "Defina a variável de ambiente para usar o endpoint /agent/chat."
        )

    return FinancingAssistantAgent(
        tools=get_tools(),
        api_key=api_key,
        model=settings.openai_model,
    )
