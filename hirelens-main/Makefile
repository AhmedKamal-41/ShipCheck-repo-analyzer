.PHONY: dev-frontend dev-backend infra-up infra-down install-frontend install-backend

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
