"""Unit tests for TesseractOCRAdapter — Tesseract binary is never invoked."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from solar_financing_assistant.application.dtos.extracted_energy_bill_data_dto import (
    ExtractedEnergyBillDataDTO,
)
from solar_financing_assistant.infrastructure.ocr.tesseract_ocr_adapter import (
    TesseractOCRAdapter,
)

# ---------------------------------------------------------------------------
# Shared fake OCR output
# ---------------------------------------------------------------------------

FAKE_BILL_TEXT = """
Nome: João da Silva
CPF: 123.456.789-09
CEP: 52000-000
Distribuidora: Neoenergia Pernambuco
Consumo mensal: 450 kWh
Valor total: R$ 380,50
Tarifa: R$ 0,8455/kWh
Referência: 2026-05
"""


# ---------------------------------------------------------------------------
# FileNotFoundError
# ---------------------------------------------------------------------------


async def test_nonexistent_file_raises_file_not_found_error() -> None:
    adapter = TesseractOCRAdapter()
    with pytest.raises(FileNotFoundError):
        await adapter.extract_energy_bill_data(Path("/nonexistent/does_not_exist.png"))


# ---------------------------------------------------------------------------
# Unsupported extension
# ---------------------------------------------------------------------------


async def test_unsupported_extension_raises_value_error(tmp_path: Path) -> None:
    bill = tmp_path / "bill.xyz"
    bill.write_text("dummy content")

    adapter = TesseractOCRAdapter()
    with pytest.raises(ValueError, match="Unsupported file type"):
        await adapter.extract_energy_bill_data(bill)


# ---------------------------------------------------------------------------
# Supported image extensions — pytesseract mocked, no binary required
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("ext", [".png", ".jpg", ".jpeg", ".webp", ".tiff", ".bmp"])
async def test_supported_image_returns_extracted_dto(
    ext: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bill = tmp_path / f"bill{ext}"
    bill.write_bytes(b"fake image bytes")

    monkeypatch.setattr("PIL.Image.open", lambda _path: MagicMock())
    monkeypatch.setattr(
        "pytesseract.image_to_string",
        lambda _image, lang: FAKE_BILL_TEXT,
    )

    adapter = TesseractOCRAdapter()
    result = await adapter.extract_energy_bill_data(bill)

    assert isinstance(result, ExtractedEnergyBillDataDTO)
    assert result.customer_name == "João da Silva"
    assert result.cpf == "12345678909"
    assert result.monthly_consumption_kwh == 450.0


async def test_image_ocr_result_is_fully_parsed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify the DTO fields match the mocked OCR text end-to-end."""
    from decimal import Decimal

    bill = tmp_path / "bill.png"
    bill.write_bytes(b"fake")

    monkeypatch.setattr("PIL.Image.open", lambda _path: MagicMock())
    monkeypatch.setattr(
        "pytesseract.image_to_string",
        lambda _image, lang: FAKE_BILL_TEXT,
    )

    adapter = TesseractOCRAdapter()
    result = await adapter.extract_energy_bill_data(bill)

    assert result.zipcode == "52000-000"
    assert result.distributor == "Neoenergia Pernambuco"
    assert result.monthly_cost_brl == Decimal("380.50")
    assert result.tariff_brl_per_kwh == Decimal("0.8455")
    assert result.reference_month == "2026-05"


# ---------------------------------------------------------------------------
# Custom parser injection
# ---------------------------------------------------------------------------


async def test_custom_parser_is_used(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Adapter must delegate to the injected parser, not create its own."""
    from solar_financing_assistant.infrastructure.ocr.energy_bill_text_parser import (
        EnergyBillTextParser,
    )

    bill = tmp_path / "bill.png"
    bill.write_bytes(b"fake")

    monkeypatch.setattr("PIL.Image.open", lambda _path: MagicMock())
    monkeypatch.setattr(
        "pytesseract.image_to_string",
        lambda _image, lang: FAKE_BILL_TEXT,
    )

    custom_parser = EnergyBillTextParser()
    parse_calls: list[str] = []
    original_parse = custom_parser.parse

    def tracking_parse(text: str) -> ExtractedEnergyBillDataDTO:
        parse_calls.append(text)
        return original_parse(text)

    custom_parser.parse = tracking_parse  # type: ignore[method-assign]

    adapter = TesseractOCRAdapter(parser=custom_parser)
    await adapter.extract_energy_bill_data(bill)

    assert len(parse_calls) == 1
    assert "João da Silva" in parse_calls[0]
