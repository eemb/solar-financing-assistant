# Solar Financing Assistant

[![CI](https://github.com/eemb/solar-financing-assistant/actions/workflows/ci.yml/badge.svg)](https://github.com/eemb/solar-financing-assistant/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![Typed](https://img.shields.io/badge/mypy-strict-brightgreen)
![License](https://img.shields.io/badge/license-MIT-green)

Backend for **residential solar financing simulation** for the Brazilian market. Starting
from a photo or PDF of an energy bill, it extracts the data via OCR, looks up the address's
solar potential through the Open-Meteo API, sizes the photovoltaic project, computes the
installments using the **Price method**, and exposes everything through a **REST API** or an
**OpenAI conversational agent**.

> **The problem.** A homeowner who wants solar panels has to guess how big a system they
> need, how much it costs, and what the monthly payment would be. This service turns a single
> energy bill into a concrete, transparent financing estimate.

**Tech stack:** Python 3.11 · FastAPI · Pydantic v2 · httpx · OpenAI SDK · Tesseract · pytest
· mypy (strict) · ruff · hexagonal architecture.

See [`docs/architecture.md`](docs/architecture.md) for the full architecture, diagrams,
request flow, design decisions, and the security model.

---

## Highlights

### Hexagonal architecture (Ports & Adapters)

The project keeps strict layer separation. The domain imports nothing external; use cases
depend on `Protocol` contracts, not implementations:

```
domain/          entities and exceptions — zero external dependencies
application/     use cases, DTOs, ports (Protocol)
infrastructure/  concrete adapters (OCR, gateways, LLM, repository)
interface/       FastAPI + CLI — delivery detail, not business logic
config/          pydantic-settings reading from .env
```

Replacing `MockOCRAdapter` with Tesseract, OpenAI Vision, or any other OCR does not change a
single use case — only the adapter.

### FastAPI with dependency injection and lifespan

- Singletons (`Settings`, `FinancingAssistantTools`, `FinancingAssistantAgent`) are created
  **once** in the application lifespan and stored in a typed `AppState` (`@dataclass`) on
  `app.state`.
- Dependencies are injected via `Depends` — fully replaceable in tests with
  `dependency_overrides`, without `lru_cache` leaking state between suites.
- `FinancingAssistantAgent` is optional: if `OPENAI_API_KEY` is missing or invalid, the API
  still starts and returns `503` only on the `/agent/chat` endpoint.
- Outbound `httpx` clients held by the gateways are closed on shutdown, so no connections leak.

### Pydantic v2 — typed schemas and strong validation

Every endpoint has typed request/response models — no generic `dict` in the public contract:

| Schema | Detail |
|--------|--------|
| `ExtractedBillPublic` | CPF masked (`123.***.***.90`) in the response |
| `ChatMessage` | `role: Literal["user", "assistant"]` — `system` blocked at the schema level |
| `AgentChatRequest` | `min_length=1, max_length=50` message list; content capped at 4,000 chars; a `model_validator` rejects conversations that don't start with `user` |
| `SolarProjectResponse`, `FinancingOfferResponse` | Typed `Decimal` fields, no opaque `dict` |
| `SimulationRequest` | `confirm: bool = False` — a simulation is persisted only with explicit confirmation |

### Layered security

| Vector | Mitigation |
|--------|------------|
| **Unauthorized access** | `X-API-Key` via `APIKeyHeader` applied globally on the router, compared with `secrets.compare_digest` (timing-safe); disabled by default in dev (`api_key: None`) |
| **Endpoint abuse** | `slowapi` reading `X-Forwarded-For` (first hop) before `request.client.host` — per-client rate limiting even behind a reverse proxy |
| **Path traversal** | A Pydantic validator blocks `..`; the handler requires the resolved path to be inside `UPLOAD_DIR` (`Path.is_relative_to`) — arbitrary absolute paths are rejected with `400` |
| **Prompt injection** | System prompt tells the model to treat extracted data as input (not instructions); the `system` role is blocked in the schema; the first message must be `user`; content is capped at 4,000 chars; OCR data is wrapped in `[DADOS EXTRAÍDOS DA CONTA]…[FIM DOS DADOS]` delimiters |
| **Data leakage** | CPF masked in every response; raw OCR text removed from `AgentChatResponse` |
| **Simulation ownership** | A per-simulation UUID token is returned in the `X-Simulation-Token` header and required on `GET /simulations/{id}` — never exposed in the JSON body |
| **Unbounded memory growth** | The repository and the token store share the same FIFO-eviction capacity, so a token never outlives or is orphaned from its simulation |
| **CORS / HTTPS** | `CORSMiddleware` configurable via `CORS_ORIGINS`; `HTTPSRedirectMiddleware` toggled by `HTTPS_REDIRECT` |

### OpenAI agent with native tool calling

No LangChain or LangGraph. `FinancingAssistantAgent` drives the tool-calling loop directly
with the async `openai` SDK:

1. Sends the conversation to the model together with the tool schemas.
2. On `finish_reason == "tool_calls"`, runs each tool through `FinancingAssistantTools`.
3. Appends the results and calls the model once more to produce the final answer.

Tools available to the agent: extract bill, complete missing fields, estimate solar project,
create simulation, check status.

### External integrations

| Service | Use |
|---------|-----|
| **BrasilAPI** | Zip-code (CEP) validation and geocoding (address → coordinates) |
| **Open-Meteo** | Historical hourly irradiation by coordinates — real PV sizing with a configurable `performance_ratio` |
| **Tesseract OCR** | Text extraction from PDF/image via `pytesseract` + `pymupdf` — replaceable by a mock for tests |

### Financial calculation

A local engine implements the **Price method** (fixed installments):
`PMT = PV × [i(1+i)^n] / [(1+i)^n − 1]`. Monthly rate and number of installments are
configurable via settings.

### Code quality and tests

- **195 tests** (unit + integration), all passing — `pytest-asyncio` with `asyncio_mode = "auto"`.
- `ruff` with rules `E, F, I, N, UP, B, SIM` — zero warnings.
- `mypy --strict` — no issues, enforced in CI.
- CI via GitHub Actions ([`.github/workflows/ci.yml`](.github/workflows/ci.yml)): ruff lint +
  format check, `mypy --strict`, and pytest with coverage.
- Local pre-commit-style check hook: [`.cursor/hooks/run-checks.sh`](.cursor/hooks/run-checks.sh).

---

## Requirements

- Python 3.11+
- Tesseract installed on the system (optional — a mock provider is available for dev/tests)

## Setup

```bash
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
.venv\Scripts\activate      # Windows

pip install -e ".[dev]"
cp .env.example .env
```

Edit `.env` as needed. Available variables are documented in `.env.example`.

## Run

### HTTP API

```bash
uvicorn solar_financing_assistant.interface.api.app:app --reload
```

Interactive docs: `http://localhost:8000/docs`

| Method | Route | Description |
|--------|-------|-------------|
| `GET` | `/health` | Application status |
| `POST` | `/energy-bills/extract` | Extract energy-bill data (rate limit: 30/min) |
| `POST` | `/energy-bills/complete` | Fill missing fields manually |
| `POST` | `/simulations` | Create a simulation (`confirm: true` required) — returns a token in `X-Simulation-Token` |
| `GET` | `/simulations/{id}` | Query status (token via `X-Simulation-Token` header) |
| `POST` | `/agent/chat` | Chat with the OpenAI agent (rate limit: 10/min) |

Quick smoke test (mock OCR — no external services needed):

```bash
# extract a mock bill (any path inside the OS temp dir works with the mock provider)
curl -X POST http://localhost:8000/energy-bills/extract \
  -H "Content-Type: application/json" \
  -d "{\"file_path\": \"$TMPDIR/bill.pdf\"}"
```

### Interactive CLI

```bash
python -m solar_financing_assistant                 # local menu
APP_MODE=agent python -m solar_financing_assistant  # OpenAI agent
```

### Docker

```bash
docker build -t solar-financing-assistant .
docker run --rm -p 8000:8000 --env-file .env solar-financing-assistant
```

The image defaults to the `mock` OCR provider, so it runs with no extra system packages. To
enable real OCR, install `tesseract-ocr`/`tesseract-ocr-por` in the image and set
`OCR_PROVIDER=tesseract`.

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | — | OpenAI key (optional — enables `/agent/chat`) |
| `OPENAI_MODEL` | `gpt-4o-mini` | Model used by the agent |
| `API_KEY` | `None` | `X-API-Key` required on requests (disabled in dev) |
| `CORS_ORIGINS` | `["*"]` | Allowed CORS origins |
| `HTTPS_REDIRECT` | `False` | Redirect HTTP → HTTPS |
| `UPLOAD_DIR` | `tempfile.gettempdir()` | Root directory for accepted file paths |
| `OCR_PROVIDER` | `mock` | OCR provider: `mock` or `tesseract` |
| `MONTHLY_RATE` | `0.019` | Monthly interest rate (1.9% p.m.) |
| `COST_PER_KWP_BRL` | `5000.00` | Installation cost per kWp (BRL) |
| `GENERATION_PER_KWP_MONTH` | `120.0` | Estimated generation per kWp/month (kWh) — fallback without coordinates |
| `PERFORMANCE_RATIO` | `0.75` | PV system performance ratio (0.70–0.85) |
| `HTTP_TIMEOUT_SECONDS` | `10.0` | Timeout for outbound HTTP calls |
| `LOG_LEVEL` | `INFO` | Log level |

## Tests & checks

```bash
pytest                   # all tests
pytest --cov             # with coverage
pytest tests/unit/       # unit only
pytest -m integration    # integration only (requires network)

ruff check . && ruff format --check .   # lint + format
mypy                                     # strict type checking
```

## Project structure

```
src/solar_financing_assistant/
├── domain/             # entities (Address, Customer, EnergyBill, SolarProject,
│                       #   FinancingOffer, FinancingSimulation) and exceptions — no external deps
├── application/
│   ├── dtos/           # data transfer objects (Pydantic)
│   ├── ports/          # Protocol contracts for infrastructure and use cases
│   └── use_cases/      # application logic (9 use cases)
├── infrastructure/
│   ├── financing/      # local Price calculation engine
│   ├── gateways/       # BrasilAPI (CEP) and Open-Meteo (solar potential)
│   ├── llm/            # OpenAI agent with tool calling + FinancingAssistantTools
│   ├── ocr/            # Tesseract and mock — selected by a factory
│   └── repositories/   # in-memory repository with FIFO eviction
├── interface/
│   ├── api/            # FastAPI — schemas, routes, auth, lifespan, AppState
│   └── cli/            # ChatCLI and AgentCLI
├── bootstrap.py        # shared dependency composition root
└── config/             # Settings via pydantic-settings (.env)
docs/
└── architecture.md     # architecture, diagrams, design decisions, security model
tests/
├── unit/               # domain, use cases, and infrastructure
└── integration/        # HTTP routes, CLI, external gateways
```

## License

[MIT](LICENSE) © Eduardo Eile
