from decimal import Decimal

from pydantic import BaseModel


class FinancingResponseDTO(BaseModel):
    simulation_id: str
    status: str
    approved_amount: Decimal
    installment_amount: Decimal
    number_of_installments: int
    monthly_rate: Decimal
    message: str
