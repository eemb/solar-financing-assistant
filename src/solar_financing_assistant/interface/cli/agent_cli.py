"""AgentCLI — terminal interface for the OpenAI-powered financing assistant."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from solar_financing_assistant.infrastructure.llm.agent import FinancingAssistantAgent

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "Você é um assistente de simulação educativa de financiamento solar residencial. "
    "Você deve guiar o usuário com clareza.\n\n"
    "Regras obrigatórias:\n"
    "1. NUNCA invente CPF, consumo, valor de conta, status ou resultado financeiro.\n"
    "2. Quando precisar de dados, peça ao usuário explicitamente.\n"
    "3. ANTES de chamar simulate_financing_from_bill, peça confirmação explícita ao usuário "
    "(ex.: 'Confirma que deseja prosseguir com a simulação? (sim/não)'). "
    "Só chame a tool após receber confirmação positiva.\n"
    "4. SEMPRE que simulate_financing_from_bill retornar um simulation_id, chame "
    "check_simulation_status com esse ID imediatamente antes de apresentar o resultado ao "
    "usuário. Nunca descreva o resultado baseado apenas na resposta da ferramenta anterior — "
    "confirme via check_simulation_status.\n"
    "5. Explique que a simulação é educativa e não constitui oferta real de crédito.\n"
    "6. Se o resultado da extração indicar que os dados são fictícios (data_source='mock'), "
    "avise claramente o usuário antes de usar esses dados."
)

_EXIT_COMMANDS = frozenset({"sair", "exit", "quit"})


class AgentCLI:
    """Interactive terminal loop backed by FinancingAssistantAgent."""

    def __init__(self, agent: FinancingAssistantAgent) -> None:
        self._agent = agent
        self._messages: list[dict[str, Any]] = [
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
