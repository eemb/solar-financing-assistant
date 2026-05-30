"""Unit tests for EnergyBillTextParser."""

from decimal import Decimal

from solar_financing_assistant.infrastructure.ocr.energy_bill_text_parser import (
    EnergyBillTextParser,
)

# ---------------------------------------------------------------------------
# Fake OCR text that resembles a real energy bill
# ---------------------------------------------------------------------------

COMPLETE_BILL_TEXT = """
FATURA DE ENERGIA ELÉTRICA

Nome: João da Silva
CPF: 123.456.789-09
CEP: 52000-000
Distribuidora: Neoenergia Pernambuco

Referência: 2026-05

Consumo mensal: 450 kWh
Tarifa: R$ 0,8455/kWh
Valor total: R$ 380,50
"""

INCOMPLETE_BILL_TEXT = """
FATURA DE ENERGIA ELÉTRICA

Algumas informações estão faltando neste documento.
"""


class TestEnergyBillTextParserComplete:
    """Parser should extract all fields from a well-formed OCR text."""

    def setup_method(self) -> None:
        self.parser = EnergyBillTextParser()
        self.result = self.parser.parse(COMPLETE_BILL_TEXT)

    def test_customer_name(self) -> None:
        assert self.result.customer_name == "João da Silva"

    def test_cpf_normalised_to_digits(self) -> None:
        # The ExtractedEnergyBillDataDTO validator strips formatting → 11 digits
        assert self.result.cpf == "12345678909"

    def test_zipcode(self) -> None:
        # No DTO validator for zipcode — stored as captured
        assert self.result.zipcode == "52000-000"

    def test_distributor(self) -> None:
        assert self.result.distributor == "Neoenergia Pernambuco"

    def test_monthly_consumption_kwh(self) -> None:
        assert self.result.monthly_consumption_kwh == 450.0

    def test_monthly_cost_brl(self) -> None:
        assert self.result.monthly_cost_brl == Decimal("380.50")

    def test_tariff_brl_per_kwh(self) -> None:
        assert self.result.tariff_brl_per_kwh == Decimal("0.8455")

    def test_reference_month(self) -> None:
        assert self.result.reference_month == "2026-05"


class TestEnergyBillTextParserIncomplete:
    """Parser must not raise exceptions for missing fields."""

    def setup_method(self) -> None:
        self.parser = EnergyBillTextParser()
        self.result = self.parser.parse(INCOMPLETE_BILL_TEXT)

    def test_does_not_raise(self) -> None:
        # Parsing itself must succeed
        assert self.result is not None

    def test_customer_name_is_none(self) -> None:
        assert self.result.customer_name is None

    def test_cpf_is_none(self) -> None:
        assert self.result.cpf is None

    def test_zipcode_is_none(self) -> None:
        assert self.result.zipcode is None

    def test_distributor_is_none(self) -> None:
        assert self.result.distributor is None

    def test_monthly_consumption_kwh_is_none(self) -> None:
        assert self.result.monthly_consumption_kwh is None

    def test_monthly_cost_brl_is_none(self) -> None:
        assert self.result.monthly_cost_brl is None

    def test_tariff_brl_per_kwh_is_none(self) -> None:
        assert self.result.tariff_brl_per_kwh is None

    def test_reference_month_is_none(self) -> None:
        assert self.result.reference_month is None


class TestEnergyBillTextParserEmpty:
    """Empty string should not crash the parser."""

    def test_empty_string(self) -> None:
        parser = EnergyBillTextParser()
        result = parser.parse("")
        assert result.customer_name is None
        assert result.cpf is None
        assert result.monthly_consumption_kwh is None
