# Solar Financing Assistant

Assistente de linha de comando para simulação de financiamento de energia solar residencial. A partir da foto de uma conta de energia, o assistente estima o sistema fotovoltaico necessário, consulta o potencial solar do endereço via Open-Meteo e calcula as parcelas pelo método Price.

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

Edite o `.env` conforme necessário. As variáveis disponíveis estão documentadas em `.env.example`.

## Executar

### CLI interativa

```bash
python -m solar_financing_assistant
```

O assistente apresenta um menu interativo com duas opções:

1. **Simular financiamento** — informa o caminho de uma conta de energia (PDF ou imagem), o sistema estima o projeto solar e calcula as parcelas
2. **Consultar status** — informe o UUID exibido ao final da simulação para ver o resultado

### Modo agente (OpenAI)

```bash
APP_MODE=agent python -m solar_financing_assistant
```

Requer `OPENAI_API_KEY` configurada no `.env`.

### API HTTP (FastAPI)

```bash
uvicorn solar_financing_assistant.interface.api.app:app --reload
```

A documentação interativa fica disponível em `http://localhost:8000/docs`.

Endpoints disponíveis:

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/health` | Status da aplicação |
| `POST` | `/energy-bills/extract` | Extrai dados de uma conta de energia |
| `POST` | `/energy-bills/complete` | Completa campos ausentes manualmente |
| `POST` | `/simulations` | Cria simulação de financiamento (`confirm: true` obrigatório) |
| `GET` | `/simulations/{id}` | Consulta status de uma simulação |
| `POST` | `/agent/chat` | Chat com o agente OpenAI (requer `OPENAI_API_KEY`) |

## Configuração

| Variável | Padrão | Descrição |
|---|---|---|
| `MONTHLY_RATE` | `0.019` | Taxa de juros mensal (1,9% a.m.) |
| `GENERATION_PER_KWP_MONTH` | `120.0` | Geração estimada por kWp/mês (kWh) — usado como fallback se o CEP não retornar coordenadas |
| `COST_PER_KWP_BRL` | `5000.00` | Custo de instalação por kWp (R$) |
| `HTTP_TIMEOUT_SECONDS` | `10.0` | Timeout para chamadas HTTP externas |
| `LOG_LEVEL` | `INFO` | Nível de log (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |

## Testes

```bash
pytest                  # todos os testes
pytest --cov            # com cobertura
pytest tests/unit/      # apenas unitários
```

## Estrutura do projeto

```
src/solar_financing_assistant/
├── domain/             # entidades e exceções — sem dependências externas
├── application/
│   ├── dtos/           # objetos de transferência de dados (Pydantic)
│   ├── ports/          # contratos (Protocol) para infraestrutura e use cases
│   └── use_cases/      # lógica de aplicação
├── infrastructure/
│   ├── financing/      # motor de cálculo Price local
│   ├── gateways/       # BrasilAPI (CEP) e Open-Meteo (potencial solar)
│   ├── ocr/            # adaptador OCR (mock — substituir pelo adaptador real)
│   └── repositories/   # repositório em memória
├── interface/
│   ├── cli/            # ChatCLI e AgentCLI — interfaces de linha de comando
│   └── api/            # FastAPI — interface HTTP
├── bootstrap.py        # Composição de dependências compartilhada
└── config/             # Settings via pydantic-settings
tests/
├── unit/
└── integration/        # a preencher com testes de adaptadores reais
```

## Arquitetura

O projeto segue arquitetura hexagonal (Ports & Adapters):

- **Domínio** não conhece nenhuma camada externa
- **Ports** definem contratos como `Protocol` — a interface layer depende de ports, não de implementações concretas
- **Adaptadores** de infraestrutura podem ser trocados sem alterar use cases (ex: substituir `MockOCRAdapter` por um adapter OpenAI Vision)
