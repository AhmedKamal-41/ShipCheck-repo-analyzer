import os

from dotenv import load_dotenv

load_dotenv()

_DEFAULT_DATABASE_URL = "postgresql+psycopg2://hirelens:hirelens@localhost:5432/hirelens"
DATABASE_URL = os.getenv("DATABASE_URL", _DEFAULT_DATABASE_URL)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

_DEFAULT_CORS = "http://localhost:3000,http://localhost:3001"
_raw = os.getenv("CORS_ORIGINS", _DEFAULT_CORS)
CORS_ORIGINS = [s.strip() for s in _raw.split(",") if s.strip()]

# Test mode: when TESTING=1, use SQLite for unit tests (faster, no setup)
TESTING = os.getenv("TESTING", "0").lower() in ("1", "true", "yes")
