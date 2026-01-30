# hirelens

[![CI](https://github.com/OWNER/REPO/actions/workflows/ci.yml/badge.svg)](https://github.com/OWNER/REPO/actions/workflows/ci.yml)

HireLens analyzes public GitHub repositories and produces a scored report plus tailored interview questions. Analysis is **read-only**: it fetches repo metadata and source files via the GitHub API and statically analyzes them—**no repository code is executed**. Replace `OWNER/REPO` in the badge with your GitHub org/repo.

---

## Problem

Hiring managers and recruiters need a quick signal of repo quality—runability, tests, CI, docs, secrets hygiene, and code structure. Manually inspecting dozens of candidate repos is tedious. HireLens automates a first-pass, rules-based analysis and outputs a report with an overall score, section breakdowns (including code analysis), and an interview pack.

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

HireLens includes comprehensive test coverage across unit, integration, E2E, contract, and performance tests.

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
