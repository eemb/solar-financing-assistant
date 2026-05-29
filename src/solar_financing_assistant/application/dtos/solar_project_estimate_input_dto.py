"""DTO for EstimateSolarProjectUseCase input."""

from decimal import Decimal

from pydantic import BaseModel


class SolarProjectEstimateInputDTO(BaseModel):
    monthly_consumption_kwh: float
    generation_per_kwp_month: float
    cost_per_kwp_brl: Decimal
