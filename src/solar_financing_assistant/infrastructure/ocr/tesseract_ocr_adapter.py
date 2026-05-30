"""Tesseract OCR adapter — wraps pytesseract for real bill text extraction."""

from __future__ import annotations

import io
import logging
from pathlib import Path

import pytesseract
from PIL import Image

from solar_financing_assistant.application.dtos.extracted_energy_bill_data_dto import (
    ExtractedEnergyBillDataDTO,
)
from solar_financing_assistant.application.ports.ocr_port import OCRPort
from solar_financing_assistant.infrastructure.ocr.energy_bill_text_parser import (
    EnergyBillTextParser,
)

logger = logging.getLogger(__name__)

_SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".tiff", ".bmp"}

_TESSERACT_NOT_FOUND_MSG = (
    "Tesseract binary not found. "
    "Please install tesseract-ocr and the Portuguese language pack:\n"
    "  Ubuntu/Debian : sudo apt install tesseract-ocr tesseract-ocr-por\n"
    "  macOS (Homebrew): brew install tesseract tesseract-lang\n"
    "  Windows       : https://github.com/UB-Mannheim/tesseract/wiki"
)


class TesseractOCRAdapter(OCRPort):
    """OCR adapter that uses Tesseract to extract text from image/PDF bills."""

    def __init__(
        self,
        parser: EnergyBillTextParser | None = None,
        language: str = "por",
        pdf_zoom: float = 2.0,
    ) -> None:
        self._parser = parser or EnergyBillTextParser()
        self._language = language
        self._pdf_zoom = pdf_zoom

    async def extract_energy_bill_data(self, file_path: Path) -> ExtractedEnergyBillDataDTO:
        if not file_path.exists():
            raise FileNotFoundError(f"Energy bill file not found: {file_path}")

        ext = file_path.suffix.lower()
        try:
            if ext == ".pdf":
                text = self._extract_text_from_pdf(file_path)
            elif ext in _SUPPORTED_IMAGE_EXTENSIONS:
                text = self._extract_text_from_image(file_path)
            else:
                raise ValueError("Unsupported file type for OCR.")
        except pytesseract.TesseractNotFoundError as exc:
            raise RuntimeError(_TESSERACT_NOT_FOUND_MSG) from exc

        return self._parser.parse(text)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _extract_text_from_pdf(self, file_path: Path) -> str:
        import fitz  # PyMuPDF — lazy import to avoid hard dependency at module level

        texts: list[str] = []
        with fitz.open(file_path) as doc:
            for page in doc:
                matrix = fitz.Matrix(self._pdf_zoom, self._pdf_zoom)
                pixmap = page.get_pixmap(matrix=matrix)
                image = Image.open(io.BytesIO(pixmap.tobytes("png")))
                page_text = pytesseract.image_to_string(image, lang=self._language)
                texts.append(page_text)
                logger.debug("OCR extracted %d chars from page %d", len(page_text), page.number)

        return "\n".join(texts)

    def _preprocess_image(self, image: "Image.Image") -> "Image.Image":
        """Upscale 2× and sharpen so Tesseract handles low-resolution scans better."""
        from PIL import ImageEnhance, ImageFilter

        w, h = image.size
        image = image.resize((w * 2, h * 2), Image.LANCZOS)
        image = ImageEnhance.Contrast(image).enhance(2.0)
        image = ImageEnhance.Sharpness(image).enhance(2.0)
        return image.filter(ImageFilter.SHARPEN)

    def _extract_text_from_image(self, file_path: Path) -> str:
        image = self._preprocess_image(Image.open(file_path).convert("L"))
        text = pytesseract.image_to_string(image, lang=self._language, config="--psm 6 --oem 3")
        logger.debug("OCR extracted %d chars from image %s", len(text), file_path.name)
        return text
