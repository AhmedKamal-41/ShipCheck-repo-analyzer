.PHONY: dev-frontend dev-backend infra-up infra-down install-frontend install-backend test-backend test-frontend test-contract test-perf test-all

dev-frontend:
	cd frontend && npm run dev

dev-backend:
	cd backend && uvicorn app.main:app --reload --port 8000

infra-up:
	docker compose -f infra/docker-compose.yml up -d

infra-down:
	docker compose -f infra/docker-compose.yml down

install-frontend:
	cd frontend && npm install

install-backend:
	cd backend && python -m venv .venv && .venv/Scripts/python -m pip install -r requirements.txt

test-backend:
	cd backend && pytest tests -v --cov=app --cov-report=term-missing --cov-report=html

test-frontend:
	cd frontend && npm run test:e2e

test-contract:
	pytest tests/contract -v

test-perf:
	cd tests/performance && k6 run health-check.js && k6 run report-endpoint.js

test-all: test-backend test-frontend test-contract
