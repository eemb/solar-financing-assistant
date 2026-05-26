"""EnergyBill entity."""

from dataclasses import dataclass, field
from uuid import UUID, uuid4


@dataclass(frozen=True)
class EnergyBill:
    monthly_consumption_kwh: float
    monthly_cost_brl: float
    distributor: str
    tariff_brl_per_kwh: float
    reference_month: str
    id: UUID = field(default_factory=uuid4)

    @property
    def annual_consumption_kwh(self) -> float:
        return self.monthly_consumption_kwh * 12

    @property
    def annual_cost_brl(self) -> float:
        return self.monthly_cost_brl * 12
