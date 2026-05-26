from decimal import Decimal

from solar_financing_assistant.application.ports.financing_engine_port import (
    FinancingEnginePort,
)
from solar_financing_assistant.domain.entities.financing_offer import FinancingOffer
from solar_financing_assistant.domain.entities.solar_project import SolarProject
from solar_financing_assistant.domain.exceptions import SimulationError


class SimulateFinancingUseCase:
    def __init__(self, financing_engine: FinancingEnginePort):
        self.financing_engine = financing_engine

    def execute(
        self,
        solar_project: SolarProject,
        number_of_installments: int = 60,
        monthly_rate: Decimal = Decimal("0.019"),
    ) -> FinancingOffer:
        if not solar_project.is_viable():
            raise SimulationError("Solar project is not viable for financing.")

        return self.financing_engine.simulate(
            project_cost=solar_project.estimated_project_cost,
            number_of_installments=number_of_installments,
            monthly_rate=monthly_rate,
        )
