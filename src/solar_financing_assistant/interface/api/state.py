"""Typed application state stored on ``app.state``."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from solar_financing_assistant.config.settings import Settings
from solar_financing_assistant.infrastructure.llm.tools import FinancingAssistantTools

if TYPE_CHECKING:
    # Imported only for type checking to keep the runtime import lazy and
    # avoid initialising the OpenAI client on module load.
    from solar_financing_assistant.infrastructure.llm.agent import FinancingAssistantAgent


@dataclass
class AppState:
    settings: Settings
    tools: FinancingAssistantTools
    agent: FinancingAssistantAgent | None
