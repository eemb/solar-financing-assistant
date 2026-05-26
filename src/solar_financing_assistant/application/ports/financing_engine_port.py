from abc import ABC, abstractmethod
from decimal import Decimal

from solar_financing_assistant.domain.entities.financing_offer import FinancingOffer


class FinancingEnginePort(ABC):
    @abstractmethod
    def simulate(
        self,
        project_cost: Decimal,
        number_of_installments: int,
        monthly_rate: Decimal,
    ) -> FinancingOffer:
        pass
