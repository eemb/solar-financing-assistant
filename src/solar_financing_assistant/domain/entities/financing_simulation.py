"""FinancingSimulation entity — aggregate root.

Intentionally NOT frozen: as the aggregate root, FinancingSimulation owns its
lifecycle. State transitions (add_offer, approve, mark_approved, mark_failed)
and lazy hydration of solar_project require in-place mutation. Callers must use
the public methods rather than assigning to fields directly.
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from .customer import Customer
from .energy_bill import EnergyBill
from .financing_offer import FinancingOffer
from .solar_project import SolarProject

logger = logging.getLogger(__name__)


class SimulationStatus(Enum):
    CREATED = "created"
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    APPROVED = "approved"
    FAILED = "failed"


@dataclass
class FinancingSimulation:
    customer: Customer | None = None
    energy_bill: EnergyBill | None = None
    solar_project: SolarProject | None = None
    _offers: list[FinancingOffer] = field(default_factory=list)
    status: SimulationStatus = SimulationStatus.PENDING
    id: UUID = field(default_factory=uuid4)

    @property
    def offers(self) -> tuple[FinancingOffer, ...]:
        """Read-only view of offers; mutate only via add_offer() / approve()."""
        return tuple(self._offers)

    def get_best_offer(
        self,
        key: Callable[[FinancingOffer], Any] | None = None,
    ) -> FinancingOffer | None:
        """Return the offer selected by *key* (default: lowest monthly installment).

        The selection criterion is a business decision: callers should supply an
        explicit *key* whenever the default does not match their context.  For
        example, to minimise total interest cost pass
        ``key=lambda o: o.total_cost``.
        """
        if not self._offers:
            return None
        effective_key = key if key is not None else lambda o: o.installment_amount
        return min(self._offers, key=effective_key)

    def add_offer(self, offer: FinancingOffer) -> None:
        self._offers.append(offer)

    def approve(self, offer: FinancingOffer) -> None:
        self.add_offer(offer)
        self.mark_approved()

    def mark_approved(self) -> None:
        self.status = SimulationStatus.APPROVED

    def mark_failed(self) -> None:
        logger.warning("Simulation %s marked as FAILED.", self.id)
        self.status = SimulationStatus.FAILED
