"""Customer entity."""

from dataclasses import dataclass, field
from uuid import UUID, uuid4

from .address import Address


@dataclass
class Customer:
    name: str
    document: str
    email: str
    phone: str
    address: Address | None = None
    id: UUID = field(default_factory=uuid4)
