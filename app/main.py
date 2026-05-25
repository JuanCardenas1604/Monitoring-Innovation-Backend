from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging_config import setup_logging
from app.core.database import engine, Base

setup_logging(debug=settings.DEBUG)
import app.models  # noqa: F401 — register all models before create_all
from app.api.v1 import auth, vehicles, users
from app.middleware.logging_middleware import LoggingMiddleware

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(LoggingMiddleware)

app.include_router(auth.router, prefix="/api")
app.include_router(vehicles.router, prefix="/api")
app.include_router(users.router, prefix="/api")


@app.get("/")
def root():
    payload = {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }
    if settings.DEBUG:
        payload["docs"] = "/docs"
    return payload


@app.get("/health")
def health():
    return {"status": "ok"}
