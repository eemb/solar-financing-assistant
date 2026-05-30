"""FinancingAssistantAgent — OpenAI tool-calling agent.

Wraps FinancingAssistantTools with an OpenAI chat loop that handles function
calling automatically.  No LangChain / LangGraph dependencies.
"""

from __future__ import annotations

import json
import logging

from openai import AsyncOpenAI

from solar_financing_assistant.infrastructure.llm.tool_schemas import TOOL_SCHEMAS
from solar_financing_assistant.infrastructure.llm.tools import FinancingAssistantTools

logger = logging.getLogger(__name__)


class FinancingAssistantAgent:
    """Single-turn agent that resolves OpenAI tool calls before returning."""

    def __init__(
        self,
        tools: FinancingAssistantTools,
        api_key: str,
        model: str,
    ) -> None:
        self._tools = tools
        self._model = model
        self._client = AsyncOpenAI(api_key=api_key)

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def run_turn(self, messages: list[dict]) -> dict:
        """Run one conversational turn, executing any tool calls along the way.

        The *messages* list is mutated in-place: the assistant tool-call
        message and all tool result messages are appended so that the full
        conversation context is preserved for the next turn.

        Returns:
            The final assistant message dict ``{"role": "assistant", "content": str}``.
        """
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=messages,  # type: ignore[arg-type]
            tools=TOOL_SCHEMAS,  # type: ignore[arg-type]
            tool_choice="auto",
        )

        message = response.choices[0].message

        if not message.tool_calls:
            return {"role": "assistant", "content": message.content or ""}

        # ------------------------------------------------------------------
        # Execute every tool call in sequence and collect results
        # ------------------------------------------------------------------
        assistant_dict: dict = {
            "role": "assistant",
            "content": message.content,
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in message.tool_calls
            ],
        }
        messages.append(assistant_dict)

        for tool_call in message.tool_calls:
            try:
                args = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError:
                args = {}
            result = await self._execute_tool(tool_call.function.name, args)
            logger.debug("Tool %s → %s", tool_call.function.name, result)

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result, ensure_ascii=False, default=str),
                }
            )

        # ------------------------------------------------------------------
        # Second model call — produce the final response
        # ------------------------------------------------------------------
        final_response = await self._client.chat.completions.create(
            model=self._model,
            messages=messages,  # type: ignore[arg-type]
            tools=TOOL_SCHEMAS,  # type: ignore[arg-type]
            tool_choice="auto",
        )

        final_message = final_response.choices[0].message
        return {"role": "assistant", "content": final_message.content or ""}

    # ------------------------------------------------------------------
    # Tool dispatch
    # ------------------------------------------------------------------

    async def _execute_tool(self, name: str, arguments: dict) -> dict:
        """Route *name* to the corresponding FinancingAssistantTools method."""
        if name == "extract_energy_bill_data":
            return await self._tools.extract_energy_bill_data(arguments["file_path"])

        if name == "complete_energy_bill_data":
            return self._tools.complete_energy_bill_data(
                arguments["extracted_bill_data"],
                arguments["manual_values"],
            )

        if name == "simulate_financing_from_bill":
            return await self._tools.simulate_financing_from_bill(arguments["extracted_bill_data"])

        if name == "check_simulation_status":
            return self._tools.check_simulation_status(arguments["simulation_id"])

        return {"status": "error", "message": f"Unknown tool: {name}"}
