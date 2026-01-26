# hirelens

[![CI](https://github.com/OWNER/REPO/actions/workflows/ci.yml/badge.svg)](https://github.com/OWNER/REPO/actions/workflows/ci.yml)

HireLens analyzes GitHub repositories and produces a scored report plus tailored interview questions. Replace `OWNER/REPO` in the badge with your GitHub org/repo.

---

## Problem

Hiring managers and recruiters need a quick signal of repo quality—runability, tests, CI, docs, secrets hygiene. Manually inspecting dozens of candidate repos is tedious. HireLens automates a first-pass, rules-based analysis and outputs a report with an overall score, section breakdowns, and an interview pack.

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
| **External** | GitHub REST API (repo metadata) |

See [docs/architecture.md](docs/architecture.md) for more detail.

---

## Local setup

1. **Start infra**  
   `docker compose -f infra/docker-compose.yml up -d`

2. **Backend**  
   - `cd backend && python -m venv .venv`  
   - `pip install -r requirements.txt` (use `.venv\Scripts\pip` on Windows)  
   - Copy `backend/.env.example` to `backend/.env`; set `DATABASE_URL` if needed, `GITHUB_TOKEN` (optional, for higher GitHub rate limits).  
   - `alembic upgrade head`  
   - `uvicorn app.main:app --reload --port 8000`

3. **Frontend**  
   - `cd frontend && npm install && npm run dev`

Use the root `Makefile` for shortcuts (`make infra-up`, `make dev-backend`, `make dev-frontend`, etc.) if you have `make`.

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
| `POST` | `/api/analyze` | Analyze a repo. Body: `{ "repo_url": "https://github.com/owner/repo" }`. Returns `{ "report_id": "..." }`. |
| `GET` | `/api/reports/{id}` | Full report (score, sections, interview pack). |
| `GET` | `/api/reports?limit=20` | List latest reports. |
| `POST` | `/api/fetch-repo` | Dev-only: fetch repo metadata (no DB). |

---

## Limitations and roadmap

**Limitations**

- GitHub rate-limits unauthenticated requests; without `GITHUB_TOKEN`, you may hit limits quickly. **Demo mode:** when rate-limited and no token, the app falls back to a bundled sample fixture so demos still work.
- Analysis is rules-based (no LLM), best-effort only.

**Roadmap**

- Async analyze job (background worker).
- Optional LLM-assisted checks.
- Auth and user-scoped reports.

---

## Repo structure

| Path | Description |
|------|-------------|
| `backend/` | FastAPI app, analyzer, GitHub client, DB models |
| `frontend/` | Next.js App Router, report UI |
| `infra/` | `docker-compose.yml` (Postgres) |
| `docs/` | Architecture, `screenshots/` placeholder |
