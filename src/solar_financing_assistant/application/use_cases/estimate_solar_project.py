"""Use case for estimating a solar project from energy consumption data."""

import logging
from decimal import Decimal

from solar_financing_assistant.application.dtos.solar_project_estimate_input_dto import (
    SolarProjectEstimateInputDTO,
)
from solar_financing_assistant.domain.entities.solar_project import SolarProject
from solar_financing_assistant.domain.exceptions import SimulationError

logger = logging.getLogger(__name__)


class EstimateSolarProjectUseCase:
    def execute(self, input_data: SolarProjectEstimateInputDTO) -> SolarProject:
        if input_data.monthly_consumption_kwh <= 0:
            raise SimulationError("monthly_consumption_kwh must be greater than zero.")
        if input_data.generation_per_kwp_month <= 0:
            raise SimulationError("generation_per_kwp_month must be greater than zero.")
        if input_data.cost_per_kwp_brl <= 0:
            raise SimulationError("cost_per_kwp_brl must be greater than zero.")

        estimated_system_kwp = (
            input_data.monthly_consumption_kwh / input_data.generation_per_kwp_month
        )
        estimated_monthly_generation_kwh = (
            estimated_system_kwp * input_data.generation_per_kwp_month
        )
        estimated_project_cost = (
            Decimal(str(estimated_system_kwp)) * input_data.cost_per_kwp_brl
        ).quantize(Decimal("0.01"))

        logger.debug(
            "Estimated solar project: kwp=%.4f, generation=%.2f kWh/month, cost=%s BRL",
            estimated_system_kwp,
            estimated_monthly_generation_kwh,
            estimated_project_cost,
        )

        return SolarProject(
            monthly_consumption_kwh=input_data.monthly_consumption_kwh,
            estimated_system_kwp=estimated_system_kwp,
            estimated_monthly_generation_kwh=estimated_monthly_generation_kwh,
            estimated_project_cost=estimated_project_cost,
        )
