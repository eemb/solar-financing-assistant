from decimal import Decimal
from typing import Protocol, runtime_checkable

from solar_financing_assistant.domain.entities.financing_offer import FinancingOffer


@runtime_checkable
class FinancingEnginePort(Protocol):
    def simulate(
        self,
        project_cost: Decimal,
        number_of_installments: int,
        monthly_rate: Decimal,
    ) -> FinancingOffer: ...
