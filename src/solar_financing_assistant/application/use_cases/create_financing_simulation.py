"""Use case for creating and persisting a new financing simulation."""

import logging
from decimal import Decimal

from solar_financing_assistant.application.ports.financing_engine_port import (
    FinancingEnginePort,
)
from solar_financing_assistant.application.ports.simulation_repository_port import (
    FinancingSimulationRepositoryPort,
)
from solar_financing_assistant.domain.entities.financing_simulation import (
    FinancingSimulation,
    SimulationStatus,
)
from solar_financing_assistant.domain.entities.solar_project import SolarProject
from solar_financing_assistant.domain.exceptions import SimulationError

logger = logging.getLogger(__name__)


class CreateFinancingSimulationUseCase:
    def __init__(
        self,
        financing_engine: FinancingEnginePort,
        repository: FinancingSimulationRepositoryPort,
    ) -> None:
        self.financing_engine = financing_engine
        self.repository = repository

    def execute(
        self,
        solar_project: SolarProject,
        number_of_installments: int = 60,
        monthly_rate: Decimal = Decimal("0.019"),
    ) -> FinancingSimulation:
        if not solar_project.is_viable():
            logger.warning(
                "Rejected non-viable project: kwp=%s, cost=%s",
                solar_project.estimated_system_kwp,
                solar_project.estimated_project_cost,
            )
            raise SimulationError("Solar project is not viable for financing.")

        simulation = FinancingSimulation(
            solar_project=solar_project,
            status=SimulationStatus.CREATED,
        )
        logger.info("Created simulation id=%s", simulation.id)

        offer = self.financing_engine.simulate(
            project_cost=solar_project.estimated_project_cost,
            number_of_installments=number_of_installments,
            monthly_rate=monthly_rate,
        )

        simulation.approve(offer)
        self.repository.save(simulation)
        logger.info(
            "Simulation id=%s approved: installment=%s x%d",
            simulation.id,
            offer.installment_amount,
            offer.number_of_installments,
        )
        return simulation
