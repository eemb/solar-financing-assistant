"""Use case for checking the status of an existing financing simulation."""

import logging
from uuid import UUID

from solar_financing_assistant.application.ports.simulation_repository_port import (
    FinancingSimulationRepositoryPort,
)
from solar_financing_assistant.domain.entities.financing_simulation import FinancingSimulation
from solar_financing_assistant.domain.exceptions import SimulationError

logger = logging.getLogger(__name__)


class CheckSimulationStatusUseCase:
    def __init__(self, repository: FinancingSimulationRepositoryPort) -> None:
        self.repository = repository

    def execute(self, id: UUID) -> FinancingSimulation:
        logger.debug("Checking status for simulation id=%s", id)
        simulation = self.repository.find_by_id(id)
        if simulation is None:
            logger.warning("Simulation not found: id=%s", id)
            raise SimulationError("Simulation not found.")
        logger.info("Simulation id=%s status: %s", simulation.id, simulation.status.value)
        return simulation
