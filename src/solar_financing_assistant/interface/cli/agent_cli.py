"""AgentCLI — terminal interface for the OpenAI-powered financing assistant."""

from __future__ import annotations

import asyncio
import logging

from solar_financing_assistant.infrastructure.llm.agent import FinancingAssistantAgent

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "Você é um assistente de simulação educativa de financiamento solar residencial. "
    "Você deve guiar o usuário com clareza. "
    "Nunca invente CPF, consumo, valor de conta, status ou resultado financeiro. "
    "Quando precisar de dados, peça ao usuário. "
    "Use as tools disponíveis para extrair conta, completar dados, simular financiamento "
    "e consultar status. "
    "Explique que a simulação é educativa e não constitui oferta real de crédito."
)

_EXIT_COMMANDS = frozenset({"sair", "exit", "quit"})


class AgentCLI:
    """Interactive terminal loop backed by FinancingAssistantAgent."""

    def __init__(self, agent: FinancingAssistantAgent) -> None:
        self._agent = agent
        self._messages: list[dict] = [
            {"role": "system", "content": _SYSTEM_PROMPT},
        ]

    def run(self) -> None:
        asyncio.run(self._run())

    async def _run(self) -> None:
        print("Assistente Solar — modo agente (OpenAI).")
        print("Digite 'sair' para encerrar.\n")

        while True:
            try:
                user_input = input("Você: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nAté logo!")
                break

            if not user_input:
                continue

            if user_input.lower() in _EXIT_COMMANDS:
                print("Até logo!")
                break

            self._messages.append({"role": "user", "content": user_input})

            try:
                response = await self._agent.run_turn(self._messages)
            except Exception as exc:
                logger.error("Agent error: %s", exc)
                print(f"\n[Erro ao contatar o assistente: {exc}]\n")
                # Remove the user message we just appended so the history stays clean
                self._messages.pop()
                continue

            self._messages.append(response)
            print(f"\nAssistente: {response['content']}\n")
