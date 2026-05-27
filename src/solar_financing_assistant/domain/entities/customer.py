"""Customer entity.

frozen=True: Customer is a value in the domain — name, document, contact info, and
address do not change in-place. Use dataclasses.replace() to produce an updated copy
(e.g. when address is resolved from a zip code lookup).
"""

import re
from dataclasses import dataclass, field
from uuid import UUID, uuid4

from solar_financing_assistant.domain.exceptions import InvalidCustomerError

from .address import Address


@dataclass(frozen=True)
class Customer:
    name: str
    document: str
    email: str
    phone: str
    address: Address | None = None
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        digits = re.sub(r"\D", "", self.document)
        if len(digits) not in (11, 14):
            raise InvalidCustomerError(
                "document must contain 11 digits (CPF) or 14 digits (CNPJ); "
                f"got {len(digits)} digit(s)."
            )
