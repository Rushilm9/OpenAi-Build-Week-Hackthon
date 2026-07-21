<div align="center">
  <img src="frontend/src/assets/arthvest-logo.png" alt="ArthVest logo" width="150" />

  # ArthVest

  ### An evidence-first AI research desk for Indian equities

  **OpenAI Build Week Hackathon · Work & Productivity**

  [![Live Demo](https://img.shields.io/badge/Live_Demo-Open_ArthVest-C45A08?style=for-the-badge)](https://openai-hack-arthvest.vercel.app/)
  [![Built with OpenAI](https://img.shields.io/badge/Built_with-OpenAI-000000?style=for-the-badge&logo=openai&logoColor=white)](https://openai.com/)
  [![Built with Codex](https://img.shields.io/badge/Built_with-Codex-111111?style=for-the-badge&logo=openai&logoColor=white)](https://openai.com/codex/)
  ![React](https://img.shields.io/badge/React_19-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)
  ![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
</div>

---

> **ArthVest turns fragmented market information into a structured, explainable research report. It coordinates specialist AI agents to discover opportunities, analyze evidence, challenge a thesis, validate risk, and return `BUY`, `SELL`, or `WAIT`—without executing a trade.**

```text
Discover → Analyze → Debate → Validate → Decide → Report
```

## 🎯 Problem

Investment research is not one search or one prompt. A serious researcher must combine macro conditions, market breadth, company fundamentals, price action, chart structure, news, sentiment, time horizon, risk, and conflicting evidence before reaching a conclusion.

> **The core problem:** researchers do not lack information; they lack a reliable system for turning scattered and conflicting information into a decision they can inspect, challenge, and reuse.

Today that process is usually:

- **Fragmented:** evidence lives across screeners, charts, feeds, filings, dashboards, and personal notes.
- **Slow:** researchers repeatedly search, copy, normalize, compare, and format the same information.
- **Biased:** an early bullish or bearish opinion can quietly shape every later step.
- **Hard to audit:** many AI tools return an answer without showing missing data, disagreement, or validation failures.
- **Overconfident:** generic assistants are optimized to answer even when the available evidence is stale, weak, or contradictory.

The result is both a productivity problem and a trust problem. Researchers spend too much time assembling information and still struggle to explain why a conclusion should be believed.

## 💡 Solution

ArthVest behaves like a coordinated research desk rather than a single chatbot. It runs two connected workflows:

1. **Market discovery** builds economic, market, news, and macro context before ranking candidates for short-, medium-, and long-term research.
2. **Company analysis** dispatches independent technical, fundamental, sentiment, and chart-pattern specialists, merges their evidence, checks the selected horizon, stages a bull-versus-bear debate, and applies deterministic validation before producing a report.

The system can return **`WAIT`** when evidence is incomplete or conviction is not justified. Refusing to manufacture certainty is a core product feature.

| Problem | ArthVest response | Research outcome |
| --- | --- | --- |
| Evidence is scattered across tools | A guided workflow gathers market, company, news, and price evidence | Less manual collection and context switching |
| One opinion creates confirmation bias | Independent specialists plus a bull-versus-bear debate | Competing explanations are considered before synthesis |
| AI answers hide uncertainty | Evidence quality, risks, counter-signals, and missing data stay visible | The researcher can audit why a verdict was produced |
| Weak evidence still produces confident language | Deterministic checks can cap confidence or return `WAIT` | Uncertainty becomes an explicit, useful output |
| Research disappears after the session | Reports are stored, searchable, and exportable | Analysis becomes durable team knowledge |

## Why ArthVest is different

| Typical market assistant | ArthVest |
| --- | --- |
| One large prompt produces one opinion | Multiple agents own independent research responsibilities |
| Starts with a ticker and ignores the environment | Builds economic, market-pulse, news, and macro context first |
| Confirms the first plausible thesis | Forces a bull-versus-bear debate before synthesis |
| Hides disagreement and missing evidence | Surfaces supporting, contradictory, stale, and unavailable evidence |
| Always tries to produce a recommendation | Uses refusal-first rules and can return `WAIT` |
| Produces disposable chat text | Saves an auditable report that can be revisited or exported |

## Product experience

### 1. Begin with the market, not a hunch

The dashboard consolidates major Indian and global indices, market breadth, volatility, commodities, and current news so company research starts in context.

![ArthVest live market dashboard](photos/openai_dashboard.png)

### 2. Build a shared research context

Before ranking a company, ArthVest shows the economic regime, market pulse, news sentiment, macro confidence, hot sectors, avoid sectors, and the reasoning behind those signals.

![ArthVest economic, market, news, and macro discovery context](photos/openai_discovery_1.png)

### 3. Rank opportunities by horizon and evidence

Candidates are organized for short-, medium-, and long-term research. Each result exposes its discovery score, catalyst, key metrics, risk count, evidence quality, and analysis state.

![ArthVest ranked opportunity discovery](photos/openai_discovery_2.png)

### 4. Inspect the decision—not just the label

The analysis report connects the final verdict to entry, target, stop loss, risk/reward, expected duration, confidence, catalysts, specialist evidence, counter-signals, and validation outcomes.

![ArthVest explainable multi-agent analysis](photos/openai_analyse.png)

### 5. Preserve research as an auditable work product

Completed recommendations remain searchable by symbol, date, signal, and horizon. Reports can be reopened and downloaded instead of disappearing at the end of a chat.

![ArthVest recommendation history and saved report](photos/openai_saved_report.png)

## End-to-end workflow

```mermaid
flowchart LR
    U["Researcher"] --> D["Discover market opportunities"]
    D --> C["Economic + market + news context"]
    C --> P["Research planner"]
    P --> T["Technical specialist"]
    P --> F["Fundamental specialist"]
    P --> S["Sentiment specialist"]
    P --> CP["Chart-pattern specialist"]
    T --> M["Merge evidence"]
    F --> M
    S --> M
    CP --> M
    M --> H["Confirm time horizon"]
    H --> B["Bull vs. bear debate"]
    B --> V["Deterministic validation"]
    V --> R["BUY / SELL / WAIT report"]
    R --> A["History + PDF export"]
```

### Agent roster

| Agent or stage | Responsibility |
| --- | --- |
| Economic | Interprets the broader economic regime and sector implications |
| Market pulse | Measures breadth, volatility, index behavior, and market health |
| News | Extracts current sentiment, themes, anomalies, and sector-level signals |
| Macro context | Combines upstream conditions into a shared research frame |
| Planner | Decides what the workflow must investigate for the selected task |
| Discovery | Screens and ranks opportunities across three time horizons |
| Technical | Evaluates trend, momentum, levels, and technical indicators |
| Fundamental | Examines business and valuation evidence |
| Sentiment | Evaluates market and company-level narrative signals |
| Chart pattern | Identifies chart structures and geometric price evidence |
| Horizon confirmation | Checks whether the evidence matches the intended holding period |
| Debate | Develops and challenges bull and bear cases |
| Decision + validator | Synthesizes evidence and enforces verdict, confidence, geometry, and risk rules |

No single specialist controls the final conclusion. The decision is produced only after independent evidence has been merged, challenged, and validated.

## 🧠 How GPT-5.6 powers ArthVest

GPT-5.6 is the runtime intelligence inside ArthVest. OpenAI models run behind a server-side model boundary implemented in `backend/app/core/model_router.py`; the browser never receives an OpenAI credential and cannot submit an arbitrary model ID.

| Runtime role | Where it is used | Model | Reasoning effort |
| --- | --- | --- | --- |
| `DISCOVERY` | Economic/news context, discovery, and technical, fundamental, sentiment, and chart evidence extraction | `gpt-5.6-terra` | Low |
| `ANALYSIS` | Research planning, macro synthesis, and the final decision narrative | `gpt-5.6-sol` | Medium |
| `ANALYSIS_DEEP` | Adversarial bull-versus-bear debate and the hardest synthesis step | `gpt-5.6-sol` | High |

### Reasoning where it matters

ArthVest does not assign maximum reasoning to every agent. That would increase latency and cost without improving every stage equally. Instead, it treats reasoning effort as an orchestration decision:

```text
LOW reasoning     → broad, repeatable evidence collection and specialist extraction
MEDIUM reasoning  → planning, cross-signal synthesis, and the final research narrative
HIGH reasoning    → adversarial debate where disagreement is most valuable
```

This tiered approach is one of the system's central innovations: use faster, lower-reasoning agents for breadth, then reserve the strongest reasoning for high-impact synthesis and challenge. All roles use OpenAI through the Responses API via `langchain-openai`, and a strict model allowlist prevents unreviewed models from entering the workflow.

GPT-5.6 is used to:

- interpret heterogeneous market evidence within a shared state;
- produce structured outputs for specialist and decision stages;
- reason across supporting and contradictory signals;
- generate explicit catalysts, risks, missing-evidence notes, and debate arguments;
- turn validated evidence into a readable research narrative.

Deterministic code remains responsible for validation rules, verdict normalization, persistence, authentication, API boundaries, and refusal behavior.

## 🛠️ How Codex was used to build ArthVest

Codex was the development partner used to build ArthVest; GPT-5.6 is the intelligence used by the running product. I developed exactly three focused Codex skills and used them as a gated engineering loop:

```text
Architect → approved system blueprint → Implement → working product → Test → verified evidence
     ↑                                                                       |
     └──────────────── failures and findings feed the next focused change ───┘
```

| Custom Codex skill | What I asked it to do | Concrete contribution |
| --- | --- | --- |
| **Architect** | Design the system before changing code | Mapped the researcher journey, separated discovery from analysis, defined agent/service boundaries and shared state, selected the reasoning tiers, and established refusal-first safety and failure paths. |
| **Implement** | Build only from the approved architecture | Created the React experience, FastAPI services, LangGraph workflows, GPT-5.6 routing, persistence, telemetry, report export, and typed frontend/backend contracts. |
| **Test** | Challenge the implementation with reproducible checks | Verified verdict consistency, evidence bounds, refusal behavior, model configuration, safe rendering, imports, builds, and the journey from discovery to a saved explainable report. |

This was not a one-shot code-generation prompt. Codex inspected the existing code, worked against explicit success criteria, traced failures across frontend and backend boundaries, and used test evidence to guide focused corrections. Human judgment remained responsible for the problem definition, product decisions, research rules, evaluation criteria, and final review.

## Safety, trust, and explainability

ArthVest is intentionally designed as research software—not an autonomous trading system.

- **No trade execution:** the platform cannot place an order or move funds.
- **Refusal-first verdicts:** missing, stale, contradictory, or low-conviction evidence can result in `WAIT`.
- **Deterministic validation:** sanity, geometry, risk/reward, confidence, and narrative consistency are checked after model reasoning.
- **Adversarial review:** bull and bear cases are developed before the final decision.
- **Visible uncertainty:** data quality, contradictory evidence, risks, and missing information remain visible to the researcher.
- **Server-side secrets:** OpenAI and data-provider credentials remain in the backend environment.
- **Restricted model routing:** arbitrary client-supplied keys and model IDs are rejected.
- **Safe rich text:** model-generated formatted content is sanitized before browser rendering.
- **Operational evidence:** agent status, latency, token use, retries, failures, and completed runs can be inspected.

## Impact

ArthVest is designed for independent equity researchers, financial analysts, wealth advisers, small research teams, and serious self-directed investors who need a repeatable research process.

The product improves knowledge-work productivity by:

- replacing repeated movement between disconnected research tools with one guided workflow;
- applying the same evidence and validation stages to every company;
- making disagreement and uncertainty reviewable rather than implicit;
- preserving completed research for comparison, audit, and export;
- letting the human spend more time reviewing assumptions and less time assembling raw information.

## Technology

| Layer | Technology |
| --- | --- |
| Web application | React 19, TypeScript, Vite, Tailwind CSS, TanStack Query |
| API | FastAPI, Pydantic, SQLAlchemy |
| Agent orchestration | LangGraph shared-state workflows |
| Intelligence | OpenAI GPT-5.6 through the Responses API |
| Market context | MCP-first access with targeted provider fallbacks |
| Supporting data | Yahoo Finance, TradingView Screener, RSS, FinVADER, and optional provider integrations |
| Persistence | PostgreSQL / Supabase |
| Reports | React PDF and jsPDF |
| Deployment | Vercel-ready frontend and Docker/Cloud Run-ready backend |

## Repository structure

```text
OpenAi-Build-Week-Hackthon/
|-- backend/
|   |-- app/
|   |   |-- agents/       # LangGraph agents, prompts, tools, and state
|   |   |-- api/routes/   # Auth, discovery, analysis, market, and telemetry APIs
|   |   |-- core/         # Model routing, validation, security, and configuration
|   |   |-- db/           # SQLAlchemy persistence models
|   |   |-- schemas/      # Pydantic contracts
|   |   `-- services/     # Data, MCP, dispatch, persistence, and logging adapters
|   |-- tests/            # Focused backend regression tests
|   `-- Dockerfile
|-- frontend/
|   |-- src/
|   |   |-- components/   # Research, evidence, reports, and shared UI
|   |   |-- pages/        # Dashboard, discovery, analysis, history, and login
|   |   |-- services/     # Typed backend API client
|   |   `-- types/        # Shared frontend contracts
|   `-- public/
|-- photos/               # Hackathon product screenshots
|-- LICENSE
`-- README.md
```

## Run locally

### Prerequisites

- Node.js 20+
- Python 3.11+
- PostgreSQL or Supabase
- An OpenAI API key with access to the configured models

### 1. Clone the repository

```bash
git clone https://github.com/Rushilm9/OpenAi-Build-Week-Hackthon.git
cd OpenAi-Build-Week-Hackthon
```

### 2. Start the backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Set at least these values in `backend/.env`:

```dotenv
OPENAI_API_KEY=your_openai_api_key
DATABASE_URL=postgresql://user:password@host:5432/database
```

Run the API:

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- Health check: `http://localhost:8000/health`
- OpenAPI documentation: `http://localhost:8000/docs`

### 3. Start the frontend

In a second terminal:

```powershell
cd frontend
npm ci
Copy-Item .env.example .env
npm run dev
```

Set the local API URL in `frontend/.env`:

```dotenv
VITE_API_BASE_URL=http://localhost:8000
```

Open `http://localhost:5173`.

## Verification

### Backend

```powershell
cd backend
python -m pytest tests/test_openai_pivot.py tests/test_evidence_summary_bounds.py test_verdict_consistency.py -q
python -m compileall -q app tests
```

### Frontend

```powershell
cd frontend
npm run test:sanitize
npm run build
npm run lint
```

The focused tests cover OpenAI routing, refusal and verdict consistency, evidence-summary bounds, and safe rendering. External model calls are not required for the deterministic regression checks.

## Core API surface

| Area | Representative endpoints |
| --- | --- |
| Health | `GET /`, `GET /health`, `GET /mcp/health` |
| Discovery | `POST /analysis/discover`, `POST /analysis/discover/jobs` |
| Analysis | `POST /analysis/analyze`, `POST /analysis/analyze_batch` |
| Results | `GET /analysis/history`, `GET /analysis/history/{rec_id}` |
| Market | `GET /market/dashboard`, `GET /market/news`, `GET /market/indices` |
| Telemetry | `GET /api/agentlogs/runs`, `GET /api/agentlogs/stats` |
| Authentication | `POST /auth/register`, `POST /auth/login`, `POST /auth/logout` |

The running OpenAPI page is the authoritative request and response reference.

## Current limitations and next steps

- Research quality depends on the freshness and availability of upstream market data.
- Model-backed workflows have higher latency and cost than a single deterministic screen.
- The current product is focused on Indian equities and research workflows.
- Outputs require independent human review and are not personalized financial advice.

Next steps include historical decision evaluation, richer source-level citations, team research workspaces, configurable evaluation datasets, and broader market coverage.

## Responsible use

`BUY`, `SELL`, and `WAIT` are research verdicts, not instructions to trade. ArthVest does not know a user's complete financial situation, risk tolerance, or regulatory obligations. Validate every output independently before making an investment decision.

## License

Released under the [MIT License](LICENSE).

<div align="center">
  <sub>Built for OpenAI Build Week · Turning fragmented market signals into structured, explainable research.</sub>
</div>
