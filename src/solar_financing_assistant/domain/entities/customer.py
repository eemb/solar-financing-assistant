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
        if len(digits) == 11:
            _validate_cpf_digits(digits)


def _validate_cpf_digits(digits: str) -> None:
    """Raise InvalidCustomerError when CPF check digits are invalid."""
    if len(set(digits)) == 1:
        raise InvalidCustomerError("CPF cannot consist of all identical digits.")

    total = sum(int(d) * (10 - i) for i, d in enumerate(digits[:9]))
    remainder = total * 10 % 11
    first_check = 0 if remainder >= 10 else remainder
    if first_check != int(digits[9]):
        raise InvalidCustomerError("CPF has invalid check digits.")

    total = sum(int(d) * (11 - i) for i, d in enumerate(digits[:10]))
    remainder = total * 10 % 11
    second_check = 0 if remainder >= 10 else remainder
    if second_check != int(digits[10]):
        raise InvalidCustomerError("CPF has invalid check digits.")
