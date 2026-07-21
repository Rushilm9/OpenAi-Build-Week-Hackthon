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

## Work & Productivity track

We selected **Work & Productivity**. The [official OpenAI Build Week challenge](https://openai.devpost.com/) defines this track as tools that make teams faster or more effective across workflows such as automation, analytics, support, sales, and operations.

ArthVest fits this track because investment research is professional knowledge work. The product does not manage a consumer portfolio or execute trades; it improves how analysts and research teams gather evidence, divide work, challenge conclusions, and produce an auditable deliverable.

| Professional workflow | Without ArthVest | With ArthVest | Productivity value |
| --- | --- | --- | --- |
| Establish market context | Open and reconcile several dashboards and feeds | Economic, market-pulse, news, and macro stages build one shared context | Less context switching and duplicated collection |
| Find candidates | Run separate screens and manually compare horizons | Discovery ranks candidates for short-, medium-, and long-term research | A repeatable shortlist with visible evidence |
| Analyze a company | One researcher sequentially studies every evidence type | Independent specialists examine technicals, fundamentals, sentiment, and chart structure | Parallel, consistent research coverage |
| Challenge a thesis | Depend on the researcher to notice personal bias | Bull and bear cases are generated before the decision | Disagreement becomes part of the workflow |
| Apply quality control | Manually inspect confidence, risk, and contradictions | Deterministic validation can cap confidence or return `WAIT` | More consistent and reviewable conclusions |
| Deliver the work | Copy findings into a separate document | Searchable history and PDF export preserve the full report | Reusable output for review and collaboration |

**Category outcome:** ArthVest helps research teams move faster by automating evidence assembly and become more effective by making every conclusion explainable, challengeable, and reusable.

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

## Three-minute judge walkthrough

The live product can be evaluated without rebuilding the project:

| Time | What to show | What it proves |
| --- | --- | --- |
| `0:00–0:25` | Open the dashboard and explain the fragmented-research problem | Clear user need and a complete product starting point |
| `0:25–0:55` | Open Discover and inspect economic, market, news, and macro context | Research begins with shared evidence instead of a ticker hunch |
| `0:55–1:25` | Run or inspect discovery across time horizons | GPT-5.6 turns broad context into ranked, explainable candidates |
| `1:25–2:15` | Open a company analysis and inspect specialist evidence, risks, debate, and verdict | Non-trivial multi-agent orchestration and visible reasoning |
| `2:15–2:40` | Show a `BUY`, `SELL`, or `WAIT` result with validation and confidence | Refusal-first safety and deterministic quality control |
| `2:40–3:00` | Open Saved Reports, then summarize Codex's Architect → Implement → Test workflow | Durable productivity output and genuine Codex usage |

## High-level architecture

ArthVest has two separate LangGraph workflows behind the same React and FastAPI application. Discovery finds evidence-backed candidates; Analysis performs deeper company research on a selected symbol. Solid arrows show workflow execution, while dashed arrows show supporting model, data, persistence, and observability services.

### Discovery architecture (F1)

```mermaid
flowchart TB
    USER["Researcher"] --> UI["React app<br/>Discover workspace"]
    UI --> API["FastAPI<br/>Discovery API"]

    subgraph F1["F1 - LangGraph discovery workflow"]
        direction LR
        START(("Start")) --> ECON["Economic Agent<br/>regime + sectors<br/>Terra / low reasoning"]
        ECON --> MARKET["Market Pulse Agent<br/>breadth + VIX + indices"]
        MARKET --> NEWS["News Agent<br/>themes + sentiment<br/>Terra / low reasoning"]
        NEWS --> MACRO["Macro Context Agent<br/>shared market frame<br/>Sol / medium reasoning"]
        MACRO --> PLAN["Planner Agent<br/>research plan<br/>Sol / medium reasoning"]
        PLAN --> DISC["Discovery Agent<br/>screen + rank candidates<br/>Terra / low reasoning"]
        DISC --> FINISH(("End"))
    end

    API --> START
    DISC --> SHORT["Short term<br/>1-2 weeks"]
    DISC --> MID["Medium term<br/>4-6 weeks"]
    DISC --> LONG["Long term<br/>3+ months"]
    SHORT --> RESULT["Ranked discovery report"]
    MID --> RESULT
    LONG --> RESULT
    RESULT --> UI

    DATA["MCP + market-data services<br/>indices, prices, news, fundamentals"] -.-> ECON
    DATA -.-> MARKET
    DATA -.-> NEWS
    DATA -.-> DISC
    ROUTER["OpenAI model router<br/>GPT-5.6 role allowlist"] -.-> ECON
    ROUTER -.-> NEWS
    ROUTER -.-> MACRO
    ROUTER -.-> PLAN
    ROUTER -.-> DISC
    STORE["PostgreSQL / Supabase<br/>runs + discoveries"] -.-> RESULT
    OBS["Agent telemetry<br/>status + latency + tokens + retries"] -.-> F1

    classDef low fill:#e8f5e9,stroke:#2e7d32,color:#111;
    classDef medium fill:#e3f2fd,stroke:#1565c0,color:#111;
    classDef service fill:#fff3e0,stroke:#c45a08,color:#111;
    class ECON,NEWS,DISC low;
    class MACRO,PLAN medium;
    class DATA,ROUTER,STORE,OBS service;
```

The Discovery graph builds context before selecting companies. Its output is not a generic stock list: each candidate is tied to a horizon, score, catalyst, risk summary, and evidence-quality state.

### Analysis architecture (F2)

```mermaid
flowchart TB
    USER["Researcher or selected discovery candidate"] --> UI["React app<br/>Analyze workspace"]
    UI --> API["FastAPI<br/>Analysis API + job dispatch"]

    subgraph F2["F2 - LangGraph analysis workflow"]
        direction TB

        subgraph CONTEXT["Context and planning"]
            direction LR
            START(("Start")) --> ECON["Economic Agent<br/>Terra / low"]
            ECON --> MARKET["Market Pulse Agent"]
            MARKET --> NEWS["News Agent<br/>Terra / low"]
            NEWS --> MACRO["Macro Context Agent<br/>Sol / medium"]
            MACRO --> PLAN["Planner Agent<br/>Sol / medium"]
        end

        subgraph SPECIALISTS["Parallel specialist analysis"]
            direction LR
            TECH["Technical Agent<br/>trend + momentum<br/>Terra / low"]
            FUND["Fundamental Agent<br/>business + valuation<br/>Terra / low"]
            SENT["Sentiment Agent<br/>narrative + signals<br/>Terra / low"]
            CHART["Chart Pattern Agent<br/>geometry + structure<br/>Terra / low"]
        end

        PLAN --> TECH
        PLAN --> FUND
        PLAN --> SENT
        PLAN --> CHART

        TECH --> MERGE["Merge signals<br/>supporting + contradictory evidence"]
        FUND --> MERGE
        SENT --> MERGE
        CHART --> MERGE

        MERGE --> HORIZON["Horizon Confirmation Agent<br/>short / medium / long fit"]
        HORIZON --> DEBATE["Bull vs. Bear Debate Agent<br/>Sol / high reasoning"]
        DEBATE --> DECISION["Decision Agent<br/>Sol / medium reasoning"]
        DECISION --> VALIDATE["Deterministic validator<br/>verdict + confidence + geometry + risk"]
        VALIDATE --> FINISH(("End"))
    end

    API --> START
    VALIDATE --> REPORT["Explainable report<br/>BUY / SELL / WAIT"]
    REPORT --> HISTORY["Saved history + PDF export"]
    HISTORY --> UI

    DATA["MCP + market-data services<br/>prices, news, fundamentals, indicators"] -.-> CONTEXT
    DATA -.-> SPECIALISTS
    ROUTER["OpenAI model router<br/>low / medium / high reasoning"] -.-> CONTEXT
    ROUTER -.-> SPECIALISTS
    ROUTER -.-> DEBATE
    ROUTER -.-> DECISION
    STORE["PostgreSQL / Supabase<br/>runs + logs + recommendations"] -.-> HISTORY
    OBS["Agent telemetry<br/>status + latency + tokens + failures"] -.-> F2

    classDef low fill:#e8f5e9,stroke:#2e7d32,color:#111;
    classDef medium fill:#e3f2fd,stroke:#1565c0,color:#111;
    classDef high fill:#f3e5f5,stroke:#7b1fa2,color:#111;
    classDef deterministic fill:#fff8e1,stroke:#f57f17,color:#111;
    classDef service fill:#fff3e0,stroke:#c45a08,color:#111;
    class ECON,NEWS,TECH,FUND,SENT,CHART low;
    class MACRO,PLAN,DECISION medium;
    class DEBATE high;
    class MARKET,MERGE,HORIZON,VALIDATE deterministic;
    class DATA,ROUTER,STORE,OBS service;
```

The Analysis graph deliberately separates evidence collection from judgment. Four specialists run independently, disagreement survives the merge, high reasoning is reserved for debate, and deterministic code validates the final model-produced decision before it reaches the report.

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

## Evidence against the judging criteria

The [official judging criteria](https://openai.devpost.com/) focus on technological implementation, design, potential impact, and quality of the idea. ArthVest provides concrete evidence for each dimension:

| Judging dimension | Evidence in ArthVest |
| --- | --- |
| **Technological implementation** | A working React/FastAPI application, two LangGraph workflows, role-based GPT-5.6 routing, parallel specialists, deterministic validation, persistence, authentication, telemetry, regression tests, and three explicit Codex development skills |
| **Design** | A coherent journey from dashboard → discovery → analysis → validated report → history, with responsive screens, visible progress, safe rich text, and PDF export |
| **Potential impact** | A specific audience—equity researchers, analysts, advisers, and small research teams—with a direct productivity case across collection, analysis, quality control, and reporting |
| **Quality of the idea** | Context-first discovery, reasoning-tier orchestration, independent specialists, adversarial debate, and `WAIT` as a valuable refusal outcome rather than a model failure |

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
