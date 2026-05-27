"""FinancingSimulation entity — aggregate root.

Intentionally NOT frozen: as the aggregate root, FinancingSimulation owns its
lifecycle. State transitions (add_offer, mark_completed, mark_failed) and lazy
hydration of solar_project require in-place mutation. Callers must use the
public methods rather than assigning to fields directly.
"""

from dataclasses import dataclass, field
from enum import Enum
from uuid import UUID, uuid4

from .customer import Customer
from .energy_bill import EnergyBill
from .financing_offer import FinancingOffer
from .solar_project import SolarProject


class SimulationStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class FinancingSimulation:
    customer: Customer
    energy_bill: EnergyBill
    solar_project: SolarProject | None = None
    offers: list[FinancingOffer] = field(default_factory=list)
    status: SimulationStatus = SimulationStatus.PENDING
    id: UUID = field(default_factory=uuid4)

    @property
    def best_offer(self) -> FinancingOffer | None:
        if not self.offers:
            return None
        return min(self.offers, key=lambda o: o.total_cost)

    def add_offer(self, offer: FinancingOffer) -> None:
        self.offers.append(offer)

    def mark_completed(self) -> None:
        self.status = SimulationStatus.COMPLETED

    def mark_failed(self) -> None:
        self.status = SimulationStatus.FAILED
