from decimal import Decimal

from pydantic import BaseModel


class ExtractedEnergyBillDataDTO(BaseModel):
    customer_name: str | None = None
    cpf: str | None = None
    zipcode: str | None = None
    distributor: str | None = None
    monthly_consumption_kwh: float | None = None
    monthly_cost_brl: Decimal | None = None
    tariff_brl_per_kwh: Decimal | None = None
    reference_month: str | None = None
