import re
from decimal import Decimal

from pydantic import BaseModel, field_validator


class ExtractedEnergyBillDataDTO(BaseModel):
    customer_name: str | None = None
    cpf: str | None = None
    zipcode: str | None = None
    distributor: str | None = None
    monthly_consumption_kwh: float | None = None
    monthly_cost_brl: Decimal | None = None
    tariff_brl_per_kwh: Decimal | None = None
    reference_month: str | None = None

    @field_validator("cpf")
    @classmethod
    def validate_cpf(cls, v: str | None) -> str | None:
        if v is None:
            return None

        digits = re.sub(r"\D", "", v)

        if len(digits) != 11:
            raise ValueError("CPF must contain exactly 11 digits.")

        if len(set(digits)) == 1:
            raise ValueError("CPF cannot consist of all identical digits.")

        total = sum(int(d) * (10 - i) for i, d in enumerate(digits[:9]))
        remainder = total * 10 % 11
        first_check = 0 if remainder >= 10 else remainder
        if first_check != int(digits[9]):
            raise ValueError("CPF has invalid check digits.")

        total = sum(int(d) * (11 - i) for i, d in enumerate(digits[:10]))
        remainder = total * 10 % 11
        second_check = 0 if remainder >= 10 else remainder
        if second_check != int(digits[10]):
            raise ValueError("CPF has invalid check digits.")

        return digits
