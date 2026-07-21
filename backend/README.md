# ArthaVest Backend

ArthaVest is a refusal-first, multi-agent equity-research API for Indian markets. It combines live market context, independent specialist analysis, adversarial debate, and deterministic validation before returning a `BUY`, `SELL`, or `WAIT` research verdict.

The system is designed for decision support—not autonomous trade execution. When evidence is missing, stale, or contradictory, the safe outcome is `WAIT` with explicit data-quality and missing-evidence fields.

## Built with Codex and GPT-5.6

Codex and GPT-5.6 were part of the engineering workflow, not just the product demo. I developed and used three focused Codex skills to move ArthVest from architecture to verified implementation while keeping each stage explicit and reviewable.

| Custom Codex skill | How it was used in ArthVest |
| --- | --- |
| **Architect** | Designed the multi-agent research system, separated discovery from company analysis, defined LangGraph state and agent boundaries, and established refusal-first verdict and safety rules. |
| **Implement** | Turned the approved architecture into FastAPI services, OpenAI model routing, specialist agents, persistence, telemetry, and frontend-facing API contracts. |
| **Test** | Exercised deterministic verdict consistency, refusal behavior, model configuration, imports, and critical integration paths before the code was prepared for submission. |

GPT-5.6 powers the application's research workloads through role-based routing: `gpt-5.6-terra` handles high-throughput discovery and context gathering, while `gpt-5.6-sol` handles planning, synthesis, decisions, and deeper adversarial analysis. Codex helped inspect the codebase, apply focused changes, trace cross-layer issues, and verify the result; I retained control of the product decisions, financial-research rules, and final review.

## Why it matters

Most market assistants are optimized to produce an answer. ArthaVest is optimized to know when the evidence is not strong enough. Its core safeguards are:

- independent economic, market-pulse, news, technical, fundamental, sentiment, and chart-pattern agents;
- an explicit horizon-confirmation step for short-, mid-, and long-term analysis;
- adversarial debate before the final decision;
- geometric, risk/reward, sanity, and narrative-consistency checks;
- a single normalized verdict vocabulary: `BUY`, `SELL`, or `WAIT`;
- per-agent run telemetry, latency, token usage, failures, and persisted recommendations.

## Product preview

| Market discovery | Evidence-backed analysis |
| --- | --- |
| ![ArthVest discovery dashboard](../photos/openai_discovery_2.png) | ![ArthVest stock analysis](../photos/openai_analyse.png) |

## Architecture

ArthaVest exposes two LangGraph workflows through FastAPI.

```mermaid
flowchart LR
    subgraph F1["F1 — Market discovery"]
        E1["Economic context"] --> M1["Market pulse"] --> N1["News"]
        N1 --> C1["Macro context"] --> P1["Planner"] --> D1["Discovery & ranking"]
    end

    subgraph F2["F2 — Stock analysis"]
        E2["Economic context"] --> M2["Market pulse"] --> N2["News"]
        N2 --> C2["Macro context"] --> P2["Planner"]
        P2 --> T["Technical"]
        P2 --> F["Fundamental"]
        P2 --> S["Sentiment"]
        P2 --> CP["Chart pattern"]
        T --> MERGE["Merge signals"]
        F --> MERGE
        S --> MERGE
        CP --> MERGE
        MERGE --> H["Horizon confirmation"] --> DB["Adversarial debate"] --> V["Validated verdict"]
    end

    DATA["MCP market-data service + local fallbacks"] --> E1
    DATA --> E2
    V --> PG["PostgreSQL / Supabase"]
```

### Model routing

The model provider boundary is implemented in `app/core/model_router.py`:

| Role | Workload | Default model | Reasoning effort |
| --- | --- | --- | --- |
| `DISCOVERY` | Discovery and high-throughput context | `gpt-5.6-terra` | Low |
| `ANALYSIS` | Planning, synthesis, and decisions | `gpt-5.6-sol` | Medium |
| `ANALYSIS_DEEP` | Adversarial debate and hardest analysis | `gpt-5.6-sol` | High |

All roles use OpenAI's Responses API through `langchain-openai`. Model IDs and
reasoning efforts are configurable through environment variables. Client-supplied
API keys and arbitrary model IDs are rejected.

### Data and persistence

- Market and macro tools use the configured MCP service first, with targeted local fallbacks where supported.
- Yahoo Finance, TradingView Screener, RSS feeds, FinVADER, and optional FRED/Finnhub/Alpha Vantage credentials supplement the research pipeline.
- SQLAlchemy persists users, runs, agent logs, discoveries, alerts, and recommendations to PostgreSQL-compatible databases.
- Local JSON output is disabled by default to keep deployments clean.

## Repository layout

```text
app/
├── agents/       # LangGraph state, workflows, specialist nodes, and prompts
├── api/routes/   # Auth, discovery/analysis, market, alerts, SMC, and telemetry APIs
├── core/         # Configuration, model routing, scheduling, security, and verdict rules
├── db/           # SQLAlchemy models
├── schemas/      # Pydantic request/response contracts
└── services/     # Market data, MCP, persistence, dispatch, and logging adapters
scripts/          # Maintenance utilities
tests/            # Focused regression tests
Dockerfile        # Production container image
```

## Quick start

### Prerequisites

- Python 3.11 or newer (the container uses Python 3.12)
- PostgreSQL or Supabase
- An OpenAI API key with access to the configured models

### 1. Create an environment

```bash
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

```bash
source .venv/bin/activate
```

### 2. Install dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 3. Configure the service

Copy the safe template and fill in your own credentials:

```powershell
Copy-Item .env.example .env
```

```bash
cp .env.example .env
```

At minimum, configure:

```dotenv
OPENAI_API_KEY=your_openai_api_key
DATABASE_URL=postgresql://user:password@host:5432/database
```

Never commit `.env` or any credential file.

### 4. Run locally

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Useful URLs:

- API health: `http://localhost:8000/health`
- OpenAPI docs: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Core API surface

| Area | Representative endpoints |
| --- | --- |
| Health | `GET /`, `GET /health`, `GET /mcp/health` |
| Discovery | `POST /analysis/discover`, `POST /analysis/discover/jobs`, `GET /analysis/discover/jobs/{job_id}` |
| Analysis | `POST /analysis/analyze`, `POST /analysis/analyze_batch`, `POST /analysis/dispatch/{run_id}` |
| Results | `GET /analysis/history`, `GET /analysis/history/{rec_id}`, `GET /analysis/latest/{symbol}` |
| Market | `GET /market/dashboard`, `GET /market/news`, `GET /market/indices` |
| Telemetry | `GET /api/agentlogs/runs`, `GET /api/agentlogs/stats`, `GET /failures` |
| Authentication | `POST /auth/register`, `POST /auth/login`, `POST /auth/logout` |

The interactive OpenAPI page is the authoritative request/response reference for the running build.

## Configuration

See `.env.example` for the complete safe template. Important groups are:

- `OPENAI_*`: API key, model roles, and request timeout;
- `DATABASE_URL`: PostgreSQL/Supabase connection;
- `MCP_*`: upstream market-data service, timeout, retries, and fallback behavior;
- `CORS_ORIGINS` and `PUBLIC_API_BASE_URL`: frontend integration;
- `DISCOVERY_HARD_*`: liquidity and price filters;
- optional financial-data provider credentials;
- `ENABLE_DEV_ROUTES=false`: keeps destructive diagnostic routes out of public deployments.

## Tests

Run the deterministic regression suite without external API calls:

```bash
python -m pytest tests/test_openai_pivot.py test_verdict_consistency.py -q
```

Useful additional checks:

```bash
python -m compileall -q app tests
python -c "from app.main import app; print(app.title)"
```

Use an isolated SQLite database for import-only checks when PostgreSQL is unavailable:

```powershell
$env:DATABASE_URL='sqlite:///:memory:'
python -c "from app.main import app; print(app.title)"
```

## Docker and deployment

Build and run the production container:

```bash
docker build -t arthavest-backend .
docker run --rm -p 10000:10000 --env-file .env arthavest-backend
```

The included GitHub Actions workflow builds the image, pushes it to Google Artifact Registry, and deploys the API to Cloud Run on pushes to `main`. Configure the required Google Cloud repository secrets before enabling that workflow.

## Security and responsible use

- Do not expose `.env`, database credentials, provider keys, or diagnostic routes.
- Keep `ENABLE_DEV_ROUTES=false` in public environments.
- Configure explicit CORS origins for every deployed frontend.
- Treat all outputs as research assistance, not personalized financial advice.
- Validate recommendations independently before making any investment decision.

## License

Released under the [MIT License](LICENSE).
