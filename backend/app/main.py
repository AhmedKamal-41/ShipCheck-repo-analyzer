from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.fetch_repo import router as api_router
from app.api.reports import router as reports_router
from app.api.routes import router
from app.core.config import CORS_ORIGINS

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router, prefix="")
app.include_router(api_router)
app.include_router(reports_router)
