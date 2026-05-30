"""Unit tests for GetMissingEnergyBillFieldsUseCase."""

from decimal import Decimal

import pytest

from solar_financing_assistant.application.dtos.extracted_energy_bill_data_dto import (
    ExtractedEnergyBillDataDTO,
)
from solar_financing_assistant.application.use_cases.get_missing_energy_bill_fields import (
    GetMissingEnergyBillFieldsUseCase,
)

_ALL_REQUIRED = [
    "customer_name",
    "cpf",
    "zipcode",
    "distributor",
    "monthly_consumption_kwh",
    "monthly_cost_brl",
    "tariff_brl_per_kwh",
    "reference_month",
]

_COMPLETE_DTO = ExtractedEnergyBillDataDTO(
    customer_name="João da Silva",
    cpf="12345678909",
    zipcode="52000-000",
    distributor="Neoenergia Pernambuco",
    monthly_consumption_kwh=450.0,
    monthly_cost_brl=Decimal("380.50"),
    tariff_brl_per_kwh=Decimal("0.8455"),
    reference_month="2026-05",
)


@pytest.fixture()
def use_case() -> GetMissingEnergyBillFieldsUseCase:
    return GetMissingEnergyBillFieldsUseCase()


def test_complete_dto_returns_empty_list(use_case: GetMissingEnergyBillFieldsUseCase) -> None:
    assert use_case.execute(_COMPLETE_DTO) == []


def test_empty_dto_returns_all_required_fields(
    use_case: GetMissingEnergyBillFieldsUseCase,
) -> None:
    missing = use_case.execute(ExtractedEnergyBillDataDTO())
    assert missing == _ALL_REQUIRED


def test_empty_string_customer_name_counts_as_missing(
    use_case: GetMissingEnergyBillFieldsUseCase,
) -> None:
    dto = _COMPLETE_DTO.model_copy(update={"customer_name": ""})
    assert "customer_name" in use_case.execute(dto)


def test_empty_string_distributor_counts_as_missing(
    use_case: GetMissingEnergyBillFieldsUseCase,
) -> None:
    dto = _COMPLETE_DTO.model_copy(update={"distributor": ""})
    assert "distributor" in use_case.execute(dto)


def test_empty_string_reference_month_counts_as_missing(
    use_case: GetMissingEnergyBillFieldsUseCase,
) -> None:
    dto = _COMPLETE_DTO.model_copy(update={"reference_month": ""})
    assert "reference_month" in use_case.execute(dto)


def test_zero_consumption_is_not_missing(
    use_case: GetMissingEnergyBillFieldsUseCase,
) -> None:
    """Zero is a legitimate value — only None is treated as missing."""
    dto = _COMPLETE_DTO.model_copy(update={"monthly_consumption_kwh": 0.0})
    assert "monthly_consumption_kwh" not in use_case.execute(dto)


def test_zero_cost_is_not_missing(use_case: GetMissingEnergyBillFieldsUseCase) -> None:
    dto = _COMPLETE_DTO.model_copy(update={"monthly_cost_brl": Decimal("0")})
    assert "monthly_cost_brl" not in use_case.execute(dto)


def test_none_consumption_is_missing(use_case: GetMissingEnergyBillFieldsUseCase) -> None:
    dto = _COMPLETE_DTO.model_copy(update={"monthly_consumption_kwh": None})
    assert "monthly_consumption_kwh" in use_case.execute(dto)


def test_none_tariff_is_missing(use_case: GetMissingEnergyBillFieldsUseCase) -> None:
    dto = _COMPLETE_DTO.model_copy(update={"tariff_brl_per_kwh": None})
    assert "tariff_brl_per_kwh" in use_case.execute(dto)


def test_partial_dto_returns_only_absent_fields(
    use_case: GetMissingEnergyBillFieldsUseCase,
) -> None:
    dto = ExtractedEnergyBillDataDTO(
        monthly_consumption_kwh=450.0,
        monthly_cost_brl=Decimal("380.50"),
        distributor="Neoenergia Pernambuco",
    )
    missing = use_case.execute(dto)
    assert "customer_name" in missing
    assert "cpf" in missing
    assert "zipcode" in missing
    assert "tariff_brl_per_kwh" in missing
    assert "reference_month" in missing
    assert "monthly_consumption_kwh" not in missing
    assert "monthly_cost_brl" not in missing
    assert "distributor" not in missing


def test_result_preserves_required_field_order(
    use_case: GetMissingEnergyBillFieldsUseCase,
) -> None:
    missing = use_case.execute(ExtractedEnergyBillDataDTO())
    assert missing == _ALL_REQUIRED
