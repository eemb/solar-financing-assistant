"""Use case for checking the status of an existing financing simulation."""

from solar_financing_assistant.application.ports.simulation_repository_port import (
    FinancingSimulationRepositoryPort,
)
from solar_financing_assistant.domain.entities.financing_simulation import FinancingSimulation
from solar_financing_assistant.domain.exceptions import SimulationError


class CheckSimulationStatusUseCase:
    def __init__(self, repository: FinancingSimulationRepositoryPort) -> None:
        self.repository = repository

    def execute(self, simulation_id: str) -> FinancingSimulation:
        simulation = self.repository.find_by_id(simulation_id)
        if simulation is None:
            raise SimulationError("Simulation not found.")
        return simulation
