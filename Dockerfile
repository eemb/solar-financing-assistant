# syntax=docker/dockerfile:1

# ---------------------------------------------------------------------------
# Solar Financing Assistant — production image
#
# Runs the FastAPI HTTP API with uvicorn. OCR defaults to the "mock" provider,
# so no Tesseract system packages are required for a demo. To enable real OCR,
# install tesseract-ocr / tesseract-ocr-por and set OCR_PROVIDER=tesseract.
# ---------------------------------------------------------------------------
FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install dependencies first (better layer caching) then the package itself.
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --upgrade pip && pip install .

# Run as an unprivileged user.
RUN useradd --create-home --uid 10001 appuser
USER appuser

EXPOSE 8000

# Bind to 0.0.0.0 so the container is reachable from the host / orchestrator.
CMD ["uvicorn", "solar_financing_assistant.interface.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
