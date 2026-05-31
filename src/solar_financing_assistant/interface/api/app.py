"""FastAPI application factory."""

from __future__ import annotations

from fastapi import FastAPI

from solar_financing_assistant.interface.api.routes import router


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    application = FastAPI(
        title="Solar Financing Assistant API",
        description=(
            "Backend HTTP para simulação de financiamento de energia solar residencial. "
            "Extrai dados de contas de energia, estima projetos fotovoltaicos e calcula "
            "parcelas pelo método Price."
        ),
        version="0.1.0",
    )
    application.include_router(router)
    return application


app = create_app()
