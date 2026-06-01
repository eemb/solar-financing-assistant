# Solar Financing Assistant

Backend para simulação de financiamento de energia solar residencial. A partir da foto ou PDF de uma conta de energia, o sistema extrai os dados via OCR, consulta potencial solar do endereço pela API Open-Meteo, dimensiona o projeto fotovoltaico, calcula as parcelas pelo método Price e expõe tudo via API REST ou agente conversacional OpenAI.

---

## Destaques de arquitetura e engenharia

### Arquitetura hexagonal (Ports & Adapters)

O projeto segue separação estrita de camadas. O domínio não importa nada externo — use cases dependem de contratos (`Protocol`), não de implementações:

```
domain/          → entidades e exceções — zero dependências externas
application/     → use cases, DTOs, ports (Protocol)
infrastructure/  → adaptadores concretos (OCR, gateways, LLM, repositório)
interface/       → FastAPI + CLI — detalhe de entrega, não lógica
config/          → pydantic-settings com leitura de .env
```

Trocar o `MockOCRAdapter` por Tesseract, OpenAI Vision ou qualquer outro OCR não altera nenhum use case — apenas o adaptador.

### FastAPI com Dependency Injection e Lifespan

- Singletons (`Settings`, `FinancingAssistantTools`, `FinancingAssistantAgent`) são criados **uma única vez** no lifespan da aplicação e armazenados em um `AppState` tipado (`@dataclass`) em `app.state`
- Dependências são injetadas via `Depends` — totalmente substituíveis em testes com `dependency_overrides`, sem `lru_cache` vazando estado entre suítes
- `FinancingAssistantAgent` é inicializado opcionalmente: se `OPENAI_API_KEY` ausente ou inválida, a API sobe sem o agente e retorna `503` apenas no endpoint `/agent/chat`

### Pydantic v2 — schemas tipados e validação forte

Todos os endpoints têm request/response com tipos concretos — nenhum `dict` genérico no contrato público:

| Schema | Detalhe |
|--------|---------|
| `ExtractedBillPublic` | CPF mascarado (`123.***.***.90`) no response |
| `ChatMessage` | `role: Literal["user", "assistant"]` — `system` bloqueado no schema |
| `AgentChatRequest` | `min_length=1, max_length=50` na lista de mensagens; conteúdo limitado a 4 000 caracteres; `model_validator` rejeita conversas que não começam com `user` |
| `SolarProjectResponse`, `FinancingOfferResponse` | Campos `Decimal` tipados, sem `dict` opaco |
| `SimulationRequest` | `confirm: bool = False` — simulação só é persistida com confirmação explícita |

### Segurança em camadas

| Vetor | Mitigação |
|-------|-----------|
| **Acesso não autorizado** | `X-API-Key` via `APIKeyHeader` aplicado globalmente no router; desativado por padrão em dev (`api_key: None`) |
| **Abuso de endpoints** | `slowapi` com `_get_client_ip` que lê `X-Forwarded-For` (primeiro segmento) antes de `request.client.host` — rate limit por usuário real mesmo atrás de proxy reverso |
| **Path traversal** | Validador Pydantic bloqueia `..`; handler valida `Path.is_relative_to(upload_dir)` via `settings.upload_dir` — path absoluto arbitrário é rejeitado com `400` |
| **Prompt injection** | System prompt instrui o modelo a tratar dados extraídos como input (não instruções); role `system` bloqueado no schema; primeira mensagem deve ser `user`; conteúdo limitado a 4 000 chars; dados OCR envolvidos em delimitadores `[DADOS EXTRAÍDOS DA CONTA]...[FIM DOS DADOS]` |
| **Vazamento de dados** | CPF mascarado em todos os responses; campo `raw` removido de `AgentChatResponse` |
| **Ownership de simulação** | Token UUID gerado na criação, retornado no header `X-Simulation-Token`; validado no `GET /simulations/{id}` via header — nunca exposto no body JSON |
| **Memory leak em tokens** | `_token_store: OrderedDict[UUID, str]` com eviction FIFO (`_MAX_TOKENS = _DEFAULT_MAX_SIZE` do repositório) — ambas as estruturas evictam na mesma cadência, impedindo que simulações se tornem públicas após o token ser descartado |
| **CORS / HTTPS** | `CORSMiddleware` configurável via `cors_origins`; `HTTPSRedirectMiddleware` ativável por `https_redirect: bool` |

### Agente OpenAI com tool calling nativo

Sem LangChain ou LangGraph. O `FinancingAssistantAgent` gerencia o loop de tool calling diretamente com a SDK `openai` assíncrona:

1. Envia mensagens ao modelo com os schemas de ferramentas
2. Detecta `finish_reason == "tool_calls"`, executa cada ferramenta via `FinancingAssistantTools`
3. Appenda resultados e chama o modelo novamente até `finish_reason == "stop"`

Ferramentas disponíveis ao agente: extração de conta, completar campos ausentes, estimar projeto solar, criar simulação, consultar status.

### Integrações externas

| Serviço | Uso |
|---------|-----|
| **BrasilAPI** | Validação e geocodificação de CEP (endereço → coordenadas) |
| **Open-Meteo** | Irradiação solar horária por coordenadas — dimensionamento real do sistema fotovoltaico com `performance_ratio` configurável |
| **Tesseract OCR** | Extração de texto de PDF/imagem via `pytesseract` + `pymupdf` — substituível por mock para testes |

### Cálculo financeiro

Motor local implementa o **método Price** (parcelas fixas): `PMT = PV × [i(1+i)^n] / [(1+i)^n − 1]`. Taxa mensal e número de parcelas são configuráveis via settings.

### Qualidade de código e testes

- **195 testes** (unit + integration), todos passando — `pytest-asyncio` com `asyncio_mode = "auto"`
- `ruff` com regras `E, F, I, N, UP, B, SIM` — zero warnings
- `mypy --strict` habilitado
- CI via GitHub Actions (`.github/workflows/ci.yml`)
- Hooks de pre-commit (`.cursor/hooks/run-checks.sh`)

---

## Requisitos

- Python 3.11+
- Tesseract instalado no sistema (opcional — modo mock disponível para dev/testes)

## Setup

```bash
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
.venv\Scripts\activate      # Windows

pip install -e ".[dev]"
cp .env.example .env
```

Edite o `.env` conforme necessário. As variáveis disponíveis estão documentadas em `.env.example`.

## Executar

### API HTTP

```bash
uvicorn solar_financing_assistant.interface.api.app:app --reload
```

Documentação interativa: `http://localhost:8000/docs`

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/health` | Status da aplicação |
| `POST` | `/energy-bills/extract` | Extrai dados de conta de energia (rate limit: 30/min) |
| `POST` | `/energy-bills/complete` | Completa campos ausentes manualmente |
| `POST` | `/simulations` | Cria simulação (`confirm: true` obrigatório) — retorna token em `X-Simulation-Token` |
| `GET` | `/simulations/{id}` | Consulta status (token via header `X-Simulation-Token`) |
| `POST` | `/agent/chat` | Chat com agente OpenAI (rate limit: 10/min) |

### CLI interativa

```bash
python -m solar_financing_assistant          # menu local
APP_MODE=agent python -m solar_financing_assistant  # agente OpenAI
```

## Configuração

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `OPENAI_API_KEY` | — | Chave OpenAI (opcional — habilita `/agent/chat`) |
| `OPENAI_MODEL` | `gpt-4o-mini` | Modelo usado pelo agente |
| `API_KEY` | `None` | Chave `X-API-Key` obrigatória nos requests (desabilitado em dev) |
| `CORS_ORIGINS` | `["*"]` | Origens permitidas no CORS |
| `HTTPS_REDIRECT` | `False` | Redireciona HTTP → HTTPS |
| `UPLOAD_DIR` | `tempfile.gettempdir()` | Diretório-raiz para paths de arquivo aceitos |
| `OCR_PROVIDER` | `mock` | Provedor OCR: `mock` ou `tesseract` |
| `MONTHLY_RATE` | `0.019` | Taxa de juros mensal (1,9% a.m.) |
| `COST_PER_KWP_BRL` | `5000.00` | Custo de instalação por kWp (R$) |
| `GENERATION_PER_KWP_MONTH` | `120.0` | Geração estimada por kWp/mês (kWh) — fallback sem coordenadas |
| `PERFORMANCE_RATIO` | `0.75` | Fator de desempenho do sistema fotovoltaico (0.70–0.85) |
| `HTTP_TIMEOUT_SECONDS` | `10.0` | Timeout para chamadas HTTP externas |
| `LOG_LEVEL` | `INFO` | Nível de log |

## Testes

```bash
pytest                   # todos os testes
pytest --cov             # com cobertura
pytest tests/unit/       # apenas unitários
pytest -m integration    # apenas integração (requer rede)
```

## Estrutura do projeto

```
src/solar_financing_assistant/
├── domain/             # entidades (Address, Customer, EnergyBill, SolarProject,
│                       #   FinancingOffer, FinancingSimulation) e exceções — sem deps externas
├── application/
│   ├── dtos/           # objetos de transferência de dados (Pydantic)
│   ├── ports/          # contratos (Protocol) para infraestrutura e use cases
│   └── use_cases/      # lógica de aplicação (9 use cases)
├── infrastructure/
│   ├── financing/      # motor de cálculo Price local
│   ├── gateways/       # BrasilAPI (CEP) e Open-Meteo (potencial solar)
│   ├── llm/            # agente OpenAI com tool calling + FinancingAssistantTools
│   ├── ocr/            # Tesseract e mock — selecionados por factory
│   └── repositories/   # repositório em memória com eviction FIFO
├── interface/
│   ├── api/            # FastAPI — schemas, rotas, auth, lifespan, AppState
│   └── cli/            # ChatCLI e AgentCLI
├── bootstrap.py        # composição de dependências compartilhada
└── config/             # Settings via pydantic-settings (.env)
tests/
├── unit/               # 26 suítes cobrindo domínio, use cases e infraestrutura
└── integration/        # rotas HTTP, CLI, gateways externos
```
