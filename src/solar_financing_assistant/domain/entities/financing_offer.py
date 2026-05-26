"""FinancingOffer entity."""

from dataclasses import dataclass, field
from uuid import UUID, uuid4


@dataclass(frozen=True)
class FinancingOffer:
    institution: str
    annual_interest_rate: float
    term_months: int
    monthly_payment_brl: float
    financed_amount_brl: float
    down_payment_brl: float = 0.0
    id: UUID = field(default_factory=uuid4)

    @property
    def total_cost_brl(self) -> float:
        return self.down_payment_brl + (self.monthly_payment_brl * self.term_months)

    @property
    def total_interest_brl(self) -> float:
        return self.total_cost_brl - self.down_payment_brl - self.financed_amount_brl
