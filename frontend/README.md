# ArthaVest Frontend

ArthaVest is an evidence-first, multi-agent equity research experience built for the OpenAI Hackathon. This repository contains the responsive web client for the ArthaVest API: it helps users discover Indian-market candidates, inspect specialist-agent evidence, run deeper analysis, and revisit saved reports.

The application is research software, not an execution platform or financial adviser. Its interface deliberately exposes confidence, supporting and contradictory evidence, data-quality signals, risk controls, and `WAIT` outcomes instead of presenting every model output as a trade.

## Built with Codex and GPT-5.6

Codex and GPT-5.6 were used throughout the build, not only as features shown in the final demo. I developed and used exactly three focused Codex skills for the project:

| Custom Codex skill | How it was used in ArthVest |
| --- | --- |
| **Architect** | Defined the end-to-end experience, frontend/backend boundary, multi-agent workflow, evidence model, safety behavior, and failure paths before implementation. |
| **Implement** | Built and integrated the React experience with the FastAPI research workflow, including discovery, analysis, progress, evidence, reports, and history. |
| **Test** | Verified safe rendering, TypeScript compilation, production builds, API contracts, and the critical user journey from discovery to an explainable saved report. |

In the running product, `gpt-5.6-terra` supports high-throughput discovery and market context, while `gpt-5.6-sol` supports planning, synthesis, decisions, and deep adversarial analysis. Codex accelerated code inspection, implementation, debugging, and verification; I remained responsible for the architecture, product judgment, research rules, and final decisions.

## Hackathon architecture

The browser is the presentation layer for the hackathon backend. It does not embed cloud credentials or call model providers directly.

```text
React + TypeScript frontend
        |
        | REST, cookie-based auth, WebSocket alerts
        v
ArthaVest FastAPI backend
        |
        +-- OpenAI GPT-5.6 multi-agent research
        +-- Arize Phoenix tracing, evaluation, and MCP workflows
        +-- market-data providers and persistent report history
```

OpenAI and Arize integrations are implemented and configured in the backend. The frontend renders the backend's research contracts, including specialist signals, debate output, validator decisions, evidence freshness, and final research posture.

## Product flow

1. **Authenticate** through the ArthaVest API.
2. **Discover** candidates across short-, mid-, and long-term horizons.
3. **Inspect evidence** and market context before requesting analysis.
4. **Analyze** an NSE/BSE symbol with the specialist-agent pipeline.
5. **Review or export** the resulting research report.
6. **Revisit saved reports** from recommendation history.

The active application routes are:

| Route | Purpose |
| --- | --- |
| `/login` | Sign in or create an account |
| `/` | View live market indices, breadth, and news |
| `/discovery` | Review horizon-based market discoveries |
| `/discovery/:symbol` | Open a discovery candidate directly |
| `/analyse` | Search for a symbol and run a full analysis |
| `/analyze/:id` | Open a saved analysis by identifier |
| `/history` | Browse saved research reports |

## Frontend stack

- React 19 and TypeScript
- Vite 8
- React Router
- TanStack Query and Axios
- Tailwind CSS
- jsPDF and React PDF for report export
- DOMPurify for safe rendering of model-generated formatting

## Run locally

### Prerequisites

- Node.js 20 or newer
- npm
- A running ArthaVest backend

### Setup

```bash
npm ci
```

Copy the environment template and point it at the API:

```bash
cp .env.example .env
```

On PowerShell:

```powershell
Copy-Item .env.example .env
```

The only required frontend setting is:

```dotenv
VITE_API_BASE_URL=https://openai-hack-arthvest-backend.onrender.com
```

Start the development server:

```bash
npm run dev
```

Vite serves the application at `http://localhost:5173` by default. Set the value to `http://localhost:8000` when running the backend locally. `VITE_BASE_URL` is also accepted as a compatibility alias. Authentication requests use browser credentials, so the backend must allow the frontend origin and cookies in its CORS/session configuration.

## Verification

```bash
npm run test:sanitize
npm run build
npm run lint
```

`test:sanitize` covers the safe rich-text renderer. `build` runs TypeScript project compilation before creating the production bundle. `lint` runs ESLint across the project.

## Production deployment

Build the static bundle with:

```bash
npm run build
```

Deploy the generated `dist/` directory to a static host and set `VITE_API_BASE_URL` at build time. The included `vercel.json` and `public/_redirects` provide single-page-application route fallback for Vercel and compatible static hosts.

Do not commit `.env`, API keys, cloud credentials, `node_modules/`, or `dist/`. All OpenAI, database, market-data, and Arize Phoenix secrets belong in the backend environment.

## Repository layout

```text
src/
|-- components/     reusable analysis, discovery, layout, and shared UI
|-- context/        authentication and WebSocket providers
|-- hooks/          query and workflow hooks
|-- pages/          routed application screens
|-- services/       typed API client
|-- types/          backend response contracts
|-- utils/          verdict and PDF export helpers
|-- App.tsx         route and application-shell composition
`-- main.tsx        React bootstrap and providers
public/             static deployment assets
```

## Security and responsible-use notes

- Model-generated formatted text is sanitized before being inserted into the DOM.
- The API client sends credentials only to the configured backend origin.
- No provider secret is required or expected in the browser.
- Outputs are research assistance and should be independently verified before financial decisions.

## License

No open-source license has been granted. All rights are reserved by the ArthaVest team.
