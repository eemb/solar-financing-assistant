"""Unit tests for CompleteEnergyBillDataUseCase."""

from decimal import Decimal

import pytest

from solar_financing_assistant.application.dtos.extracted_energy_bill_data_dto import (
    ExtractedEnergyBillDataDTO,
)
from solar_financing_assistant.application.use_cases.complete_energy_bill_data import (
    CompleteEnergyBillDataUseCase,
)


@pytest.fixture()
def use_case() -> CompleteEnergyBillDataUseCase:
    return CompleteEnergyBillDataUseCase()


# ---------------------------------------------------------------------------
# Filling absent fields
# ---------------------------------------------------------------------------


def test_fills_absent_string_fields(use_case: CompleteEnergyBillDataUseCase) -> None:
    dto = ExtractedEnergyBillDataDTO()
    result = use_case.execute(dto, {"customer_name": "Maria Souza", "distributor": "CPFL"})
    assert result.customer_name == "Maria Souza"
    assert result.distributor == "CPFL"


def test_fills_absent_reference_month(use_case: CompleteEnergyBillDataUseCase) -> None:
    dto = ExtractedEnergyBillDataDTO()
    result = use_case.execute(dto, {"reference_month": "2026-05"})
    assert result.reference_month == "2026-05"


def test_fills_consumption_as_float(use_case: CompleteEnergyBillDataUseCase) -> None:
    dto = ExtractedEnergyBillDataDTO()
    result = use_case.execute(dto, {"monthly_consumption_kwh": "450"})
    assert result.monthly_consumption_kwh == 450.0
    assert isinstance(result.monthly_consumption_kwh, float)


def test_fills_consumption_with_comma_decimal(use_case: CompleteEnergyBillDataUseCase) -> None:
    dto = ExtractedEnergyBillDataDTO()
    result = use_case.execute(dto, {"monthly_consumption_kwh": "450,5"})
    assert result.monthly_consumption_kwh == 450.5


def test_fills_cost_as_decimal(use_case: CompleteEnergyBillDataUseCase) -> None:
    dto = ExtractedEnergyBillDataDTO()
    result = use_case.execute(dto, {"monthly_cost_brl": "380,50"})
    assert result.monthly_cost_brl == Decimal("380.50")
    assert isinstance(result.monthly_cost_brl, Decimal)


def test_fills_cost_with_dot_decimal(use_case: CompleteEnergyBillDataUseCase) -> None:
    dto = ExtractedEnergyBillDataDTO()
    result = use_case.execute(dto, {"monthly_cost_brl": "380.50"})
    assert result.monthly_cost_brl == Decimal("380.50")


def test_fills_tariff_as_decimal_with_comma(use_case: CompleteEnergyBillDataUseCase) -> None:
    dto = ExtractedEnergyBillDataDTO()
    result = use_case.execute(dto, {"tariff_brl_per_kwh": "0,8455"})
    assert result.tariff_brl_per_kwh == Decimal("0.8455")


def test_fills_cost_with_thousands_separator(use_case: CompleteEnergyBillDataUseCase) -> None:
    dto = ExtractedEnergyBillDataDTO()
    result = use_case.execute(dto, {"monthly_cost_brl": "1.380,50"})
    assert result.monthly_cost_brl == Decimal("1380.50")


# ---------------------------------------------------------------------------
# Not overwriting existing OCR values
# ---------------------------------------------------------------------------


def test_does_not_overwrite_existing_string_field(use_case: CompleteEnergyBillDataUseCase) -> None:
    dto = ExtractedEnergyBillDataDTO(customer_name="João da Silva")
    result = use_case.execute(dto, {"customer_name": "Outro Nome"})
    assert result.customer_name == "João da Silva"


def test_does_not_overwrite_existing_consumption(use_case: CompleteEnergyBillDataUseCase) -> None:
    dto = ExtractedEnergyBillDataDTO(monthly_consumption_kwh=450.0)
    result = use_case.execute(dto, {"monthly_consumption_kwh": "999"})
    assert result.monthly_consumption_kwh == 450.0


def test_does_not_overwrite_existing_cost(use_case: CompleteEnergyBillDataUseCase) -> None:
    dto = ExtractedEnergyBillDataDTO(monthly_cost_brl=Decimal("380.50"))
    result = use_case.execute(dto, {"monthly_cost_brl": "999,00"})
    assert result.monthly_cost_brl == Decimal("380.50")


def test_does_not_overwrite_existing_tariff(use_case: CompleteEnergyBillDataUseCase) -> None:
    dto = ExtractedEnergyBillDataDTO(tariff_brl_per_kwh=Decimal("0.8455"))
    result = use_case.execute(dto, {"tariff_brl_per_kwh": "9,9999"})
    assert result.tariff_brl_per_kwh == Decimal("0.8455")


# ---------------------------------------------------------------------------
# Full round-trip
# ---------------------------------------------------------------------------


def test_partial_dto_completed_with_all_manual_values(
    use_case: CompleteEnergyBillDataUseCase,
) -> None:
    partial = ExtractedEnergyBillDataDTO(
        monthly_consumption_kwh=450.0,
        monthly_cost_brl=Decimal("380.50"),
        distributor="Neoenergia Pernambuco",
    )
    manual = {
        "customer_name": "Maria Souza",
        "cpf": "529.982.247-25",
        "zipcode": "52000-000",
        "tariff_brl_per_kwh": "0,8455",
        "reference_month": "2026-05",
    }
    result = use_case.execute(partial, manual)

    assert result.customer_name == "Maria Souza"
    assert result.cpf == "52998224725"  # normalised by DTO validator
    assert result.zipcode == "52000-000"
    assert result.tariff_brl_per_kwh == Decimal("0.8455")
    assert result.reference_month == "2026-05"
    # OCR values untouched
    assert result.monthly_consumption_kwh == 450.0
    assert result.monthly_cost_brl == Decimal("380.50")
    assert result.distributor == "Neoenergia Pernambuco"


def test_empty_manual_value_stores_none_for_absent_string(
    use_case: CompleteEnergyBillDataUseCase,
) -> None:
    dto = ExtractedEnergyBillDataDTO()
    result = use_case.execute(dto, {"customer_name": ""})
    assert result.customer_name is None
