# shipcheck

ShipCheck analyzes public GitHub repositories and produces a scored report plus tailored interview questions. Analysis is **read-only**: it fetches repo metadata and source files via the GitHub API and statically analyzes them—**no repository code is executed**.

---

## Problem

Hiring managers and recruiters need a quick signal of repo quality—runability, tests, CI, docs, secrets hygiene, and code structure. Manually inspecting dozens of candidate repos is tedious. ShipCheck automates a first-pass, rules-based analysis and outputs a report with an overall score, section breakdowns (including code analysis), and an interview pack.

---

## Architecture

```
[Browser] --> [Next.js] --> [FastAPI] --> [Postgres]
                  |              |
                  v              v
            [Tailwind]    [GitHub REST API]
```

| Component | Stack |
|-----------|--------|
| **Frontend** | Next.js (App Router), TypeScript, Tailwind |
| **Backend** | FastAPI, SQLAlchemy, Alembic |
| **Infra** | Docker Compose, Postgres |
| **External** | GitHub REST API (repo metadata + tree/blobs for code analysis) |

See [docs/architecture.md](docs/architecture.md) for more detail.

---

## Local setup

1. **Start infra**  
   `docker compose -f infra/docker-compose.yml up -d`

2. **Backend**  
   - `cd backend && python -m venv .venv`  
   - Activate the venv (e.g. `.venv\Scripts\activate` on Windows, `source .venv/bin/activate` on macOS/Linux).  
   - `pip install -r requirements.txt`  
   - Copy `backend/.env.example` to `backend/.env`; set `DATABASE_URL` if needed, `CORS_ORIGINS` (e.g. `http://localhost:3000`), and optionally `GITHUB_TOKEN` for higher GitHub API rate limits.  
   - `alembic upgrade head`  
   - `uvicorn app.main:app --reload --port 8000`

3. **Frontend**  
   - `cd frontend && npm install && npm run dev`  
   - Optionally create `frontend/.env.local` with `NEXT_PUBLIC_API_BASE=http://localhost:8000` so the app talks to your local backend (this is the default if unset).

Use the root `Makefile` for shortcuts (`make infra-up`, `make dev-backend`, `make dev-frontend`, etc.) if you have `make`. Open **http://localhost:3000** in your browser.

---

## Screenshots

*(screenshots to be added)*

| Screen | Placeholder |
|--------|-------------|
| Home | ![Home](docs/screenshots/home.png) |
| Report | ![Report](docs/screenshots/report.png) |

---

## API endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/health` | Liveness |
| `GET` | `/db-check` | DB connectivity (debug) |
| `POST` | `/api/analyze` | Analyze a public GitHub repo (read-only; no code execution). Body: `{ "repo_url": "https://github.com/owner/repo" }`. Returns `{ "report_id": "..." }`. |
| `GET` | `/api/reports/{id}` | Full report (score, sections including Code Analysis, interview pack). |
| `GET` | `/api/reports?limit=20` | List latest reports. |
| `POST` | `/api/fetch-repo` | Dev-only: fetch repo metadata (no DB). |

---

## Report sections

Reports include:

- **Runability** – README install/run hints, Docker support.
- **Engineering Quality** – Tests, CI, lint/format, dependency pinning.
- **Secrets Safety** – .env.example, possible secret patterns in key files.
- **Documentation** – README length and structure.
- **Code Analysis** – Language breakdown, framework detection (FastAPI/Flask/Next/Express), endpoint discovery, architecture hints, quality signals (lint/format/typecheck/test), and security signals (secrets + dangerous patterns). Evidence includes file path and line range. Large repos are truncated by file/byte limits.
- **Architecture** – Import-graph metrics: circular imports, god modules (high fan-in), and orphan modules (unused, non-entry-point files).

---

## Code analysis (v2)

v2 adds rules-based static analysis on top of the original file-existence checks. Every finding is weighted, every recommendation is structured, and the overall score is composed from six weighted categories.

### What's analyzed

- **Cyclomatic complexity** (Python via `radon`, JS/TS via `tree-sitter`)
- **Function length and nesting depth**
- **Type safety** (TypeScript `: any` and `as any` counts)
- **Code smells** (empty `except` blocks, `eval`, `console.log` in production code, magic numbers)
- **Dependency hygiene** (unpinned, unused, missing dependencies)
- **Architecture** (import graph, circular imports, god modules, orphan modules)

### Scoring

Every finding is weighted by:

- **Severity** — LOW (0.3), MEDIUM (0.6), HIGH (1.0)
- **Confidence** — analyzer's certainty (0.5–1.0)
- **Scope** — how widespread the issue is (0.2–1.0, scaling with occurrence count)

The overall score is a weighted average across six categories:

| Category          | Weight |
|-------------------|--------|
| Runability        | 20%    |
| Testing & CI      | 20%    |
| Security & Deps   | 20%    |
| Maintainability   | 15%    |
| Architecture      | 15%    |
| Documentation     | 10%    |

### Recommendations

Each finding answers four questions:

- **WHAT** was found
- **WHERE** in the code
- **WHY** it matters (the cost in maintenance, security, or risk)
- **HOW** to fix it

The frontend renders this structured shape; the v=1 API endpoint returns a flat string for backward compatibility.

### API versioning

`GET /api/reports/{id}` accepts a `?v=` query parameter:

- `?v=1` (default): each `recommendation` is a flat string. Existing clients are unaffected.
- `?v=2`: each `recommendation` is a `{ what, where, why, how }` dict. The frontend uses this path.

### What v2 does NOT do

- Doesn't execute repo code (still 100% static analysis)
- Doesn't use LLMs
- Doesn't classify repo type or change weights based on a "role" — every repo is judged on the same rubric

---

## v2 changelog

- **`radon` + `tree-sitter` integration** — real cyclomatic complexity metrics for Python and JS/TS.
- **Severity-weighted categorical scoring** — six categories with explicit weights, each finding weighted by severity × confidence × scope.
- **Structured recommendations** — every finding has a what / where / why / how breakdown rendered in the UI.
- **Architecture analysis** — import graph via `networkx`: circular imports, god modules, orphan modules.
- **`v=1` / `v=2` API versioning** — `findings_v2` column persists the structured shape; `?v=` query parameter selects the response shape; legacy clients unchanged.

---

## Limitations and roadmap

**Limitations**

- Only **public** GitHub repos; GitHub API read-only. No repository code is executed.
- GitHub rate-limits unauthenticated requests; without `GITHUB_TOKEN`, you may hit limits quickly. **Demo mode:** when rate-limited and no token, the app falls back to a bundled sample fixture so demos still work.
- Analysis is rules-based (no LLM), best-effort only. Code analysis uses AST/regex only; large repos may be partially analyzed due to limits.

**Roadmap**

- Async analyze job (background worker).
- Optional LLM-assisted checks.
- Auth and user-scoped reports.

---

## Testing

ShipCheck includes comprehensive test coverage across unit, integration, E2E, contract, and performance tests.

### Running Tests

**Backend Tests:**
```bash
make test-backend
# or
cd backend && pytest tests -v --cov=app --cov-report=term-missing
```

**Frontend E2E Tests:**
```bash
make test-frontend
# or
cd frontend && npm run test:e2e
```

**Contract Tests:**
```bash
make test-contract
# or
pytest tests/contract -v
```

**Performance Tests:**
```bash
make test-perf
# or
cd tests/performance && k6 run health-check.js
```

**All Tests:**
```bash
make test-all
```

### Test Structure

- **Unit Tests** (`backend/tests/unit/`): Fast, isolated tests for individual functions
- **Integration Tests** (`backend/tests/integration/`): API endpoint and database tests
- **E2E Tests** (`frontend/tests/e2e/`): Playwright tests for user workflows
- **Contract Tests** (`tests/contract/`): API response schema validation
- **Performance Tests** (`tests/performance/`): k6 load tests

### CI/CD

Tests run automatically on every push and pull request via GitHub Actions. See [`.github/workflows/ci.yml`](.github/workflows/ci.yml) for the full pipeline.

**CI Jobs:**
- `backend-tests`: Runs pytest with coverage (≥80% required)
- `frontend-build`: Lints and builds Next.js app
- `frontend-tests`: Runs Playwright E2E tests
- `contract-tests`: Validates API contracts
- `performance-tests`: Runs k6 scripts (optional/manual trigger)

**Test Reports:**
- Coverage reports: Available as artifacts in GitHub Actions
- Playwright reports: HTML reports uploaded as artifacts
- View latest run: [GitHub Actions](https://github.com/OWNER/REPO/actions)

### Test Documentation

- [Test Plan](docs/qa/test-plan.md): Comprehensive testing strategy
- [Test Matrix](docs/qa/test-matrix.md): Feature coverage by test type
- [Manual Test Cases](docs/qa/manual-test-cases.md): 15+ detailed manual test scenarios
- [Bug Report Template](docs/qa/bug-report-template.md): Standardized bug reporting
- [Release Checklist](docs/qa/release-checklist.md): Pre/post-release verification

---

## Repo structure

| Path | Description |
|------|-------------|
| `backend/` | FastAPI app, analyzer, GitHub client, repo ingest, DB models |
| `backend/app/analyzers/code/` | Code analyzers (language, FastAPI/JS routes, quality, security) |
| `backend/app/core/repo_limits.py` | File/byte limits and path filters for ingestion |
| `backend/app/services/repo_ingest.py` | Tree + blob fetch and text file ingestion |
| `backend/tests/` | Backend unit and integration tests |
| `frontend/` | Next.js App Router, report UI |
| `frontend/tests/` | Frontend E2E tests (Playwright) |
| `tests/contract/` | API contract tests |
| `tests/performance/` | k6 performance test scripts |
| `infra/` | `docker-compose.yml` (Postgres) |
| `docs/` | Architecture, QA documentation, screenshots |
