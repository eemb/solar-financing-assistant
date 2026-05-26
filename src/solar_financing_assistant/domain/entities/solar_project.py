"""SolarProject entity."""

from dataclasses import dataclass, field
from decimal import Decimal
from uuid import UUID, uuid4


@dataclass(frozen=True)
class SolarProject:
    monthly_consumption_kwh: float
    estimated_system_kwp: float
    estimated_monthly_generation_kwh: float
    estimated_project_cost: Decimal
    id: UUID = field(default_factory=uuid4)

    def is_viable(self) -> bool:
        return (
            self.estimated_monthly_generation_kwh > 0
            and self.estimated_project_cost > 0
        )
