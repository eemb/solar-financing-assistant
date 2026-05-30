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
    r"CEP[:\s:]*(\d{5}-?\d{3})",
    re.IGNORECASE,
)

# Matches explicit label OR known distributor brand name anywhere in the text.
_DISTRIBUTOR_EXPLICIT = re.compile(
    r"(?:Distribuidora|Concession[aá]ria|Empresa)[:\s]+([^\n]+)",
    re.IGNORECASE,
)
_DISTRIBUTOR_BRAND = re.compile(
    r"(?:Ampla|Enel|Cemig|Copel|Energisa|Neoenergia|Elektro|AES|CPFL|Coelba|Celpe"
    r"|Cosern|Coelce|Ceal|Celg|CEB|Energipe|Celesc|RGE|CEEE|EDP|Light|Equatorial)"
    r"[^\n]{0,60}",
    re.IGNORECASE,
)

_CONSUMPTION_PATTERNS = [
    re.compile(r"Consumo\s+mensal[:\s]+(\d+(?:[.,]\d+)?)\s*kWh", re.IGNORECASE),
    re.compile(r"Consumo[:\s]+(\d+(?:[.,]\d+)?)\s*kWh", re.IGNORECASE),
    re.compile(r"Consumo[:\s]+(\d+(?:[.,]\d+)?)", re.IGNORECASE),
    re.compile(r"CONSUMO[^\d]*(\d{3,}(?:[.,]\d+)?)\s*kWh", re.IGNORECASE),
    re.compile(r"(\d{3,}(?:[.,]\d+)?)\s*kWh", re.IGNORECASE),
]

# Priority order: specific "Valor da Fatura" label first, then generic Total/R$
_COST_PATTERNS = [
    re.compile(
        # Require at least one decimal separator to avoid matching bare annotation numbers
        r"Valor\s+da\s+Fatura[^\d]{0,30}R?\$?\s*(\d+[.,]\d+)",
        re.IGNORECASE | re.DOTALL,
    ),
    re.compile(
        r"(?:Valor\s+total|Total\s+a\s+pagar)[:\s]+R?\$?\s*(\d+(?:[.,]\d+)*)",
        re.IGNORECASE,
    ),
    re.compile(r"R\$\s*(\d+[.,]\d+)", re.IGNORECASE),
]

_TARIFF_PATTERNS = [
    re.compile(
        r"Tarifa[:\s]+R?\$?\s*(\d+[.,]\d+)\s*/?\s*kWh",
        re.IGNORECASE,
    ),
    re.compile(r"R\$\s*(\d+[.,]\d+)\s*/kWh", re.IGNORECASE),
    re.compile(r"Tarifa[:\s]+(\d+[.,]\d+)", re.IGNORECASE),
]

# YYYY-MM or Portuguese month name + year (e.g. "Mai/2018", "Maio/2018")
# Cross-line: "REFERÊNCIA\n\nMai/2018" is common in OCR output
_REFERENCE_PATTERNS = [
    re.compile(r"Refer[eê]ncia[:\s]+(\d{4}-\d{2})", re.IGNORECASE),
    re.compile(r"M[eê]s\s+de\s+refer[eê]ncia[:\s]+(\d{4}-\d{2})", re.IGNORECASE),
    re.compile(r"Compet[eê]ncia[:\s]+(\d{4}-\d{2})", re.IGNORECASE),
    re.compile(
        r"Refer[eê]ncia[:\s]+"
        r"(Jan|Fev|Mar|Abr|Mai|Jun|Jul|Ago|Set|Out|Nov|Dez)[a-z]*/(\d{4})",
        re.IGNORECASE,
    ),
    # "REFERÊNCIA" label with month/year up to 3 lines below (cross-line)
    re.compile(
        r"REFER[EÊ]NCIA[\s\S]{0,60}?"
        r"(Jan|Fev|Mar|Abr|Mai|Jun|Jul|Ago|Set|Out|Nov|Dez)[a-z]*/(\d{4})",
        re.IGNORECASE,
    ),
    # Standalone MM/YYYY (only if 4-digit year, to avoid matching dates like 16/06/2018)
    re.compile(r"\b(0[1-9]|1[0-2])/(\d{4})\b"),
]

_PT_MONTHS = {
    "jan": "01",
    "fev": "02",
    "mar": "03",
    "abr": "04",
    "mai": "05",
    "jun": "06",
    "jul": "07",
    "ago": "08",
    "set": "09",
    "out": "10",
    "nov": "11",
    "dez": "12",
}


def _to_decimal(raw: str) -> Decimal:
    """Convert a Brazilian-formatted number string to Decimal.

    Handles thousands dot + comma decimal (e.g. "1.380,50") and
    plain comma decimal (e.g. "380,50"). Plain dot decimal ("380.50")
    is also accepted.
    """
    if "," in raw:
        raw = raw.replace(".", "").replace(",", ".")
    return Decimal(raw)


def _normalize_reference(raw: str) -> str | None:
    """Convert Portuguese month/year strings to YYYY-MM.

    Accepts: 'Mai/2018', '05/2018', 'Maio/2018', '2026-05'.
    """
    raw = raw.strip()
    # Already YYYY-MM
    if re.fullmatch(r"\d{4}-\d{2}", raw):
        return raw
    # MM/YYYY
    m = re.fullmatch(r"(\d{1,2})/(\d{4})", raw)
    if m:
        return f"{m.group(2)}-{int(m.group(1)):02d}"
    # Mon/YYYY or Month/YYYY (Portuguese)
    m = re.fullmatch(r"([A-Za-záéíóúãõâêôç]{3,5})/(\d{4})", raw, re.IGNORECASE)
    if m:
        month_key = m.group(1)[:3].lower()
        month_num = _PT_MONTHS.get(month_key)
        if month_num:
            return f"{m.group(2)}-{month_num}"
    return None


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
        match = _DISTRIBUTOR_EXPLICIT.search(text)
        if match:
            return match.group(1).strip()
        match = _DISTRIBUTOR_BRAND.search(text)
        if match:
            # Keep only the first "word run" to avoid capturing OCR noise
            brand_line = match.group(0).strip()
            # Truncate at the first digit or known noise separator
            clean = re.split(r"\d|[|\\]", brand_line)[0].strip().rstrip(".,;:-")
            return clean if clean else None
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
                # Patterns with two capture groups (month name + year)
                if match.lastindex and match.lastindex >= 2:
                    try:
                        raw = f"{match.group(1)}/{match.group(2)}"
                    except IndexError:
                        raw = match.group(1)
                else:
                    raw = match.group(1)
                result = _normalize_reference(raw)
                if result:
                    return result
        return None
