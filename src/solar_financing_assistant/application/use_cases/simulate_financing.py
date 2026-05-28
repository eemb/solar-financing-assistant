import logging
from decimal import Decimal

from solar_financing_assistant.application.ports.financing_engine_port import (
    FinancingEnginePort,
)
from solar_financing_assistant.domain.entities.financing_offer import FinancingOffer
from solar_financing_assistant.domain.entities.solar_project import SolarProject
from solar_financing_assistant.domain.exceptions import SimulationError

logger = logging.getLogger(__name__)


class SimulateFinancingUseCase:
    def __init__(
        self,
        financing_engine: FinancingEnginePort,
        monthly_rate: Decimal | None = None,
    ) -> None:
        self.financing_engine = financing_engine
        if monthly_rate is not None:
            self.monthly_rate = monthly_rate
        else:
            from solar_financing_assistant.infrastructure.config import settings
            self.monthly_rate = settings.monthly_rate

    def execute(
        self,
        solar_project: SolarProject,
        number_of_installments: int = 60,
    ) -> FinancingOffer:
        if not solar_project.is_viable():
            logger.warning(
                "Rejected non-viable project: kwp=%s, cost=%s",
                solar_project.estimated_system_kwp,
                solar_project.estimated_project_cost,
            )
            raise SimulationError("Solar project is not viable for financing.")

        logger.info(
            "Simulating financing: cost=%s, installments=%d, rate=%s",
            solar_project.estimated_project_cost,
            number_of_installments,
            self.monthly_rate,
        )
        offer = self.financing_engine.simulate(
            project_cost=solar_project.estimated_project_cost,
            number_of_installments=number_of_installments,
            monthly_rate=self.monthly_rate,
        )
        logger.info("Offer result: installment=%s x%d", offer.installment_amount, offer.number_of_installments)
        return offer
