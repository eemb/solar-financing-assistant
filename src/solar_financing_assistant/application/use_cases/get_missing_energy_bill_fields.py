"""Use case that identifies which required energy bill fields are absent."""

from solar_financing_assistant.application.dtos.extracted_energy_bill_data_dto import (
    ExtractedEnergyBillDataDTO,
)

_REQUIRED_FIELDS: tuple[str, ...] = (
    "customer_name",
    "cpf",
    "zipcode",
    "distributor",
    "monthly_consumption_kwh",
    "monthly_cost_brl",
    "tariff_brl_per_kwh",
    "reference_month",
)

# Fields stored as str — missing when None OR empty string.
_STRING_FIELDS: frozenset[str] = frozenset(
    {"customer_name", "cpf", "zipcode", "distributor", "reference_month"}
)


class GetMissingEnergyBillFieldsUseCase:
    """Return the list of required fields that are absent in *extracted_bill*."""

    def execute(self, extracted_bill: ExtractedEnergyBillDataDTO) -> list[str]:
        missing: list[str] = []
        for field in _REQUIRED_FIELDS:
            value = getattr(extracted_bill, field)
            if field in _STRING_FIELDS:
                if not value:  # None or empty string
                    missing.append(field)
            else:
                if value is None:
                    missing.append(field)
        return missing
