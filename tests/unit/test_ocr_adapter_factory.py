"""Unit tests for create_ocr_adapter factory."""

import pytest

from solar_financing_assistant.infrastructure.ocr.mock_ocr_adapter import MockOCRAdapter
from solar_financing_assistant.infrastructure.ocr.ocr_adapter_factory import create_ocr_adapter
from solar_financing_assistant.infrastructure.ocr.tesseract_ocr_adapter import (
    TesseractOCRAdapter,
)


def test_mock_provider_returns_mock_adapter() -> None:
    adapter = create_ocr_adapter("mock")
    assert isinstance(adapter, MockOCRAdapter)


def test_tesseract_provider_returns_tesseract_adapter() -> None:
    adapter = create_ocr_adapter("tesseract")
    assert isinstance(adapter, TesseractOCRAdapter)


def test_provider_is_case_insensitive_upper() -> None:
    adapter = create_ocr_adapter("MOCK")
    assert isinstance(adapter, MockOCRAdapter)


def test_provider_is_case_insensitive_mixed() -> None:
    adapter = create_ocr_adapter("Tesseract")
    assert isinstance(adapter, TesseractOCRAdapter)


def test_provider_strips_surrounding_whitespace() -> None:
    adapter = create_ocr_adapter("  TESSERACT  ")
    assert isinstance(adapter, TesseractOCRAdapter)


def test_invalid_provider_raises_value_error() -> None:
    with pytest.raises(ValueError, match="Unsupported OCR provider"):
        create_ocr_adapter("openai")


def test_empty_provider_raises_value_error() -> None:
    with pytest.raises(ValueError, match="Unsupported OCR provider"):
        create_ocr_adapter("")


def test_returned_mock_adapter_satisfies_ocr_port() -> None:
    from solar_financing_assistant.application.ports.ocr_port import OCRPort

    adapter = create_ocr_adapter("mock")
    assert isinstance(adapter, OCRPort)


def test_returned_tesseract_adapter_satisfies_ocr_port() -> None:
    from solar_financing_assistant.application.ports.ocr_port import OCRPort

    adapter = create_ocr_adapter("tesseract")
    assert isinstance(adapter, OCRPort)
