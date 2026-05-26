"""FinancingOffer entity."""

from dataclasses import dataclass, field
from decimal import Decimal
from uuid import UUID, uuid4


@dataclass(frozen=True)
class FinancingOffer:
    approved_amount: Decimal
    installment_amount: Decimal
    number_of_installments: int
    monthly_rate: Decimal
    id: UUID = field(default_factory=uuid4)

    @property
    def total_cost(self) -> Decimal:
        return self.installment_amount * self.number_of_installments

    def is_valid(self) -> bool:
        return (
            self.approved_amount > 0
            and self.installment_amount > 0
            and self.number_of_installments > 0
            and self.monthly_rate >= 0
        )
