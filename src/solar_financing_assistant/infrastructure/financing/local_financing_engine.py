from decimal import ROUND_HALF_UP, Decimal

from solar_financing_assistant.application.ports.financing_engine_port import (
    FinancingEnginePort,
)
from solar_financing_assistant.domain.entities.financing_offer import FinancingOffer
from solar_financing_assistant.domain.exceptions import SimulationError


class LocalFinancingEngine(FinancingEnginePort):
    def simulate(
        self,
        project_cost: Decimal,
        number_of_installments: int,
        monthly_rate: Decimal,
    ) -> FinancingOffer:
        if project_cost <= 0:
            raise SimulationError("Project cost must be greater than zero.")

        if number_of_installments <= 0:
            raise SimulationError("Number of installments must be greater than zero.")

        if monthly_rate < 0:
            raise SimulationError("Monthly rate cannot be negative.")

        installment_amount = self._calculate_price_installment(
            principal=project_cost,
            monthly_rate=monthly_rate,
            installments=number_of_installments,
        )

        return FinancingOffer(
            approved_amount=project_cost,
            installment_amount=installment_amount,
            number_of_installments=number_of_installments,
            monthly_rate=monthly_rate,
        )

    def _calculate_price_installment(
        self,
        principal: Decimal,
        monthly_rate: Decimal,
        installments: int,
    ) -> Decimal:
        if monthly_rate == 0:
            return (principal / Decimal(installments)).quantize(
                Decimal("0.01"),
                rounding=ROUND_HALF_UP,
            )

        one = Decimal("1")
        factor = (one + monthly_rate) ** installments

        installment = principal * monthly_rate * factor / (factor - one)

        return installment.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
