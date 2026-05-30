"""Factory that instantiates the correct OCR adapter from a provider name."""

from solar_financing_assistant.application.ports.ocr_port import OCRPort
from solar_financing_assistant.infrastructure.ocr.mock_ocr_adapter import MockOCRAdapter
from solar_financing_assistant.infrastructure.ocr.tesseract_ocr_adapter import (
    TesseractOCRAdapter,
)


def create_ocr_adapter(provider: str) -> OCRPort:
    """Return an :class:`OCRPort` implementation for *provider*.

    Args:
        provider: Case-insensitive provider name.  Supported values: ``"mock"``,
            ``"tesseract"``.

    Raises:
        ValueError: When *provider* is not a recognised value.
    """
    normalised = provider.lower().strip()

    if normalised == "mock":
        return MockOCRAdapter()
    if normalised == "tesseract":
        return TesseractOCRAdapter()

    raise ValueError(f"Unsupported OCR provider: {provider}")
