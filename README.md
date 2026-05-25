# Solar Financing Assistant

Assistente conversacional para simulação de financiamento de energia solar residencial.

## Requisitos

- Python 3.11+

## Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

pip install -e ".[dev]"
cp .env.example .env
```

## Executar

```bash
python -m solar_financing_assistant
```

## Testes

```bash
pytest
```

## Estrutura

```
src/
  solar_financing_assistant/
    __init__.py
    __main__.py
tests/
  unit/
  integration/
```
