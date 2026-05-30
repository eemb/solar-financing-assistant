"""Script manual para testar o OCR em uma imagem de fatura de energia."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Permite rodar de qualquer diretório sem instalar o pacote
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from solar_financing_assistant.infrastructure.ocr.tesseract_ocr_adapter import (
    TesseractOCRAdapter,
)


def _preprocess(path: Path):
    """Retorna imagem em escala de cinza, 2× upscale, contraste e nitidez aumentados."""
    from PIL import Image, ImageEnhance, ImageFilter

    img = Image.open(path).convert("L")
    w, h = img.size
    img = img.resize((w * 2, h * 2), Image.LANCZOS)
    img = ImageEnhance.Contrast(img).enhance(2.0)
    img = ImageEnhance.Sharpness(img).enhance(2.0)
    img = img.filter(ImageFilter.SHARPEN)
    return img


async def main(image_path: str) -> None:
    import pytesseract

    path = Path(image_path)
    if not path.exists():
        print(f"[ERRO] Arquivo não encontrado: {path}")
        sys.exit(1)

    print(f"Processando: {path.name}")

    # --- texto bruto sem pré-processamento ---
    from PIL import Image

    print("\n" + "=" * 60)
    print("TEXTO BRUTO (sem pré-processamento):")
    print("=" * 60)
    raw = pytesseract.image_to_string(Image.open(path), lang="por", config="--psm 6 --oem 3")
    print(raw)

    # --- texto bruto com pré-processamento ---
    print("\n" + "=" * 60)
    print("TEXTO BRUTO (com pré-processamento):")
    print("=" * 60)
    preprocessed = _preprocess(path)
    raw_enhanced = pytesseract.image_to_string(preprocessed, lang="por", config="--psm 6 --oem 3")
    print(raw_enhanced)

    # --- campos extraídos pelo parser ---
    print("\n" + "=" * 60)
    print("CAMPOS EXTRAÍDOS PELO PARSER:")
    print("-" * 60)

    adapter = TesseractOCRAdapter(language="por")
    result = await adapter.extract_energy_bill_data(path)

    print(f"{'Nome do cliente':<30}: {result.customer_name or '—'}")
    print(f"{'CPF':<30}: {result.cpf or '—'}")
    print(f"{'CEP':<30}: {result.zipcode or '—'}")
    print(f"{'Distribuidora':<30}: {result.distributor or '—'}")
    print(f"{'Consumo mensal (kWh)':<30}: {result.monthly_consumption_kwh or '—'}")
    print(f"{'Custo mensal (R$)':<30}: {result.monthly_cost_brl or '—'}")
    print(f"{'Tarifa (R$/kWh)':<30}: {result.tariff_brl_per_kwh or '—'}")
    print(f"{'Mês de referência':<30}: {result.reference_month or '—'}")
    print("-" * 60)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python scripts/test_ocr_image.py <caminho_da_imagem>")
        sys.exit(1)
    asyncio.run(main(sys.argv[1]))
