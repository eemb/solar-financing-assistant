"""Use case that fills absent energy bill fields with manually supplied values."""

from decimal import Decimal

from solar_financing_assistant.application.dtos.extracted_energy_bill_data_dto import (
    ExtractedEnergyBillDataDTO,
)

_DECIMAL_FIELDS: frozenset[str] = frozenset({"monthly_cost_brl", "tariff_brl_per_kwh"})


def _to_decimal(raw: str) -> Decimal:
    """Convert a Brazilian-formatted number string to Decimal.

    Accepts both ``"380,50"`` (comma decimal) and ``"380.50"`` (dot decimal).
    Also handles thousands separators, e.g. ``"1.380,50"``.
    """
    if "," in raw:
        return Decimal(raw.replace(".", "").replace(",", "."))
    return Decimal(raw)


def _is_filled(value: object) -> bool:
    """Return True when *value* is considered already present (not missing)."""
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    return True  # numeric, Decimal — any non-None value counts


class CompleteEnergyBillDataUseCase:
    """Merge OCR-extracted data with manually supplied field values.

    Fields that already have a value from OCR are **never** overwritten.
    Only absent fields (None or empty string) are filled from *manual_values*.
    """

    def execute(
        self,
        extracted_bill: ExtractedEnergyBillDataDTO,
        manual_values: dict[str, str],
    ) -> ExtractedEnergyBillDataDTO:
        data: dict[str, object] = extracted_bill.model_dump()

        for field, raw_value in manual_values.items():
            if _is_filled(data.get(field)):
                continue  # already set by OCR — do not overwrite

            if field == "monthly_consumption_kwh":
                data[field] = float(raw_value.replace(",", "."))
            elif field in _DECIMAL_FIELDS:
                data[field] = _to_decimal(raw_value)
            else:
                data[field] = raw_value.strip() or None

        return ExtractedEnergyBillDataDTO.model_validate(data)
