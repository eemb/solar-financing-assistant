"""SolarProject entity."""

from dataclasses import dataclass, field
from uuid import UUID, uuid4


@dataclass(frozen=True)
class SolarProject:
    system_size_kwp: float
    estimated_generation_kwh_year: float
    panel_count: int
    installation_cost_brl: float
    estimated_savings_brl_year: float
    id: UUID = field(default_factory=uuid4)

    @property
    def payback_years(self) -> float:
        if self.estimated_savings_brl_year <= 0:
            return float("inf")
        return self.installation_cost_brl / self.estimated_savings_brl_year
