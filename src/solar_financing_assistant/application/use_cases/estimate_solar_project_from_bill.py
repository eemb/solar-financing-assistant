"""Use case: estimate a solar project from extracted energy bill data."""

import logging
from decimal import Decimal

import httpx

from solar_financing_assistant.application.dtos.extracted_energy_bill_data_dto import (
    ExtractedEnergyBillDataDTO,
)
from solar_financing_assistant.application.dtos.solar_project_estimate_input_dto import (
    SolarProjectEstimateInputDTO,
)
from solar_financing_assistant.application.use_cases.estimate_solar_project import (
    EstimateSolarProjectUseCase,
)
from solar_financing_assistant.application.use_cases.get_solar_potential import (
    GetSolarPotentialUseCase,
)
from solar_financing_assistant.application.use_cases.validate_address import (
    ValidateAddressUseCase,
)
from solar_financing_assistant.domain.entities.solar_project import SolarProject
from solar_financing_assistant.domain.exceptions import InvalidAddressError, SimulationError

logger = logging.getLogger(__name__)


class EstimateSolarProjectFromBillUseCase:
    def __init__(
        self,
        validate_address_use_case: ValidateAddressUseCase,
        get_solar_potential_use_case: GetSolarPotentialUseCase,
        estimate_solar_project_use_case: EstimateSolarProjectUseCase,
        fallback_generation_per_kwp_month: float,
        cost_per_kwp_brl: Decimal,
    ) -> None:
        self._validate_address = validate_address_use_case
        self._get_solar_potential = get_solar_potential_use_case
        self._estimate_solar_project = estimate_solar_project_use_case
        self._fallback_generation_per_kwp_month = fallback_generation_per_kwp_month
        self._cost_per_kwp_brl = cost_per_kwp_brl

    async def execute(self, extracted_bill: ExtractedEnergyBillDataDTO) -> SolarProject:
        project, _ = await self._execute_internal(extracted_bill)
        return project

    async def execute_with_metadata(
        self, extracted_bill: ExtractedEnergyBillDataDTO
    ) -> tuple[SolarProject, str]:
        """Return ``(solar_project, solar_potential_source)``.

        ``solar_potential_source`` is ``"api"`` when real irradiation data was
        obtained from the solar gateway, or ``"fallback"`` when the default
        ``generation_per_kwp_month`` was used (no zipcode, invalid address, or
        network error).
        """
        return await self._execute_internal(extracted_bill)

    async def _execute_internal(
        self, extracted_bill: ExtractedEnergyBillDataDTO
    ) -> tuple[SolarProject, str]:
        if (
            extracted_bill.monthly_consumption_kwh is None
            or extracted_bill.monthly_consumption_kwh <= 0
        ):
            raise SimulationError("Monthly consumption is required to estimate solar project.")

        generation_per_kwp_month = self._fallback_generation_per_kwp_month
        solar_potential_source = "fallback"

        if extracted_bill.zipcode:
            try:
                address = await self._validate_address.execute(extracted_bill.zipcode)
                if address.latitude is not None and address.longitude is not None:
                    solar_potential = await self._get_solar_potential.execute(
                        address.latitude,
                        address.longitude,
                    )
                    generation_per_kwp_month = (
                        solar_potential.estimated_daily_generation_kwh_per_kwp * 30
                    )
                    solar_potential_source = "api"
                    logger.info(
                        "Solar potential from (%.4f, %.4f): %.2f kWh/kWp/month",
                        address.latitude,
                        address.longitude,
                        generation_per_kwp_month,
                    )
            except (httpx.HTTPError, InvalidAddressError):
                logger.warning(
                    "Could not retrieve solar potential; falling back to %.2f kWh/kWp/month",
                    self._fallback_generation_per_kwp_month,
                )
                generation_per_kwp_month = self._fallback_generation_per_kwp_month
                solar_potential_source = "fallback"

        project = self._estimate_solar_project.execute(
            SolarProjectEstimateInputDTO(
                monthly_consumption_kwh=extracted_bill.monthly_consumption_kwh,
                generation_per_kwp_month=generation_per_kwp_month,
                cost_per_kwp_brl=self._cost_per_kwp_brl,
            )
        )
        return project, solar_potential_source
