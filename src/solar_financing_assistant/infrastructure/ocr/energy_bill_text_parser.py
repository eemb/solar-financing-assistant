"""Parser that extracts structured energy bill fields from raw OCR text."""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

from solar_financing_assistant.application.dtos.extracted_energy_bill_data_dto import (
    ExtractedEnergyBillDataDTO,
)

# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

_NAME_PATTERN = re.compile(
    r"(?:Nome|Cliente|Titular)[:\s]+([^\n]+)",
    re.IGNORECASE,
)

_CPF_PATTERN = re.compile(
    r"CPF[:\s]*(\d{3}[.\s]?\d{3}[.\s]?\d{3}[-\s]?\d{2}|\d{11})",
    re.IGNORECASE,
)

_ZIPCODE_PATTERN = re.compile(
    r"CEP[:\s]*(\d{5}-?\d{3})",
    re.IGNORECASE,
)

_DISTRIBUTOR_PATTERN = re.compile(
    r"(?:Distribuidora|Concession[aá]ria|Empresa)[:\s]+([^\n]+)",
    re.IGNORECASE,
)

_CONSUMPTION_PATTERNS = [
    re.compile(r"Consumo\s+mensal[:\s]+(\d+(?:[.,]\d+)?)\s*kWh", re.IGNORECASE),
    re.compile(r"Consumo[:\s]+(\d+(?:[.,]\d+)?)\s*kWh", re.IGNORECASE),
    re.compile(r"Consumo[:\s]+(\d+(?:[.,]\d+)?)", re.IGNORECASE),
    re.compile(r"(\d+(?:[.,]\d+)?)\s*kWh", re.IGNORECASE),
]

_COST_PATTERNS = [
    re.compile(
        r"(?:Valor\s+total|Total\s+a\s+pagar|Total)[:\s]+R?\$?\s*(\d+(?:[.,]\d+)*)",
        re.IGNORECASE,
    ),
    re.compile(r"R\$\s*(\d+(?:[.,]\d+)+)", re.IGNORECASE),
]

_TARIFF_PATTERNS = [
    re.compile(
        r"Tarifa[:\s]+R?\$?\s*(\d+[.,]\d+)\s*/?\s*kWh",
        re.IGNORECASE,
    ),
    re.compile(r"R\$\s*(\d+[.,]\d+)\s*/kWh", re.IGNORECASE),
    re.compile(r"Tarifa[:\s]+(\d+[.,]\d+)", re.IGNORECASE),
]

_REFERENCE_PATTERNS = [
    re.compile(r"Refer[eê]ncia[:\s]+(\d{4}-\d{2})", re.IGNORECASE),
    re.compile(r"M[eê]s\s+de\s+refer[eê]ncia[:\s]+(\d{4}-\d{2})", re.IGNORECASE),
    re.compile(r"Compet[eê]ncia[:\s]+(\d{4}-\d{2})", re.IGNORECASE),
]


def _to_decimal(raw: str) -> Decimal:
    """Convert a Brazilian-formatted number string to Decimal.

    Handles thousands dot + comma decimal (e.g. "1.380,50") and
    plain comma decimal (e.g. "380,50"). Plain dot decimal ("380.50")
    is also accepted.
    """
    if "," in raw:
        raw = raw.replace(".", "").replace(",", ".")
    return Decimal(raw)


class EnergyBillTextParser:
    """Extract structured fields from the raw text produced by OCR."""

    def parse(self, text: str) -> ExtractedEnergyBillDataDTO:
        return ExtractedEnergyBillDataDTO(
            customer_name=self._extract_customer_name(text),
            cpf=self._extract_cpf(text),
            zipcode=self._extract_zipcode(text),
            distributor=self._extract_distributor(text),
            monthly_consumption_kwh=self._extract_consumption(text),
            monthly_cost_brl=self._extract_cost(text),
            tariff_brl_per_kwh=self._extract_tariff(text),
            reference_month=self._extract_reference_month(text),
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _extract_customer_name(self, text: str) -> str | None:
        match = _NAME_PATTERN.search(text)
        if match:
            return match.group(1).strip()
        return None

    def _extract_cpf(self, text: str) -> str | None:
        match = _CPF_PATTERN.search(text)
        if match:
            return match.group(1).strip()
        return None

    def _extract_zipcode(self, text: str) -> str | None:
        match = _ZIPCODE_PATTERN.search(text)
        if match:
            return match.group(1).strip()
        return None

    def _extract_distributor(self, text: str) -> str | None:
        match = _DISTRIBUTOR_PATTERN.search(text)
        if match:
            return match.group(1).strip()
        return None

    def _extract_consumption(self, text: str) -> float | None:
        for pattern in _CONSUMPTION_PATTERNS:
            match = pattern.search(text)
            if match:
                try:
                    return float(match.group(1).replace(",", "."))
                except ValueError:
                    continue
        return None

    def _extract_cost(self, text: str) -> Decimal | None:
        for pattern in _COST_PATTERNS:
            match = pattern.search(text)
            if match:
                try:
                    return _to_decimal(match.group(1))
                except InvalidOperation:
                    continue
        return None

    def _extract_tariff(self, text: str) -> Decimal | None:
        for pattern in _TARIFF_PATTERNS:
            match = pattern.search(text)
            if match:
                try:
                    return _to_decimal(match.group(1))
                except InvalidOperation:
                    continue
        return None

    def _extract_reference_month(self, text: str) -> str | None:
        for pattern in _REFERENCE_PATTERNS:
            match = pattern.search(text)
            if match:
                return match.group(1)
        return None
