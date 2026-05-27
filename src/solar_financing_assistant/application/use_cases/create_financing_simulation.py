"""Use case for creating and persisting a new financing simulation."""

from decimal import Decimal
from uuid import uuid4

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
            raise SimulationError("Solar project is not viable for financing.")

        simulation = FinancingSimulation(
            simulation_id=f"SIM-{uuid4()}",
            solar_project=solar_project,
            status=SimulationStatus.CREATED,
        )

        offer = self.financing_engine.simulate(
            project_cost=solar_project.estimated_project_cost,
            number_of_installments=number_of_installments,
            monthly_rate=monthly_rate,
        )

        simulation.approve(offer)
        self.repository.save(simulation)

        return simulation
