"""Ω JARBIS Enterprise - FastAPI Application."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1.endpoints.mobile_chat import router as mobile_chat_router
from app.api.v1.endpoints.recipes import router as recipes_router
from app.api.v1.endpoints.inventory import router as inventory_router
from app.api.v1.endpoints.events import router as events_router
from app.api.v1.endpoints.financial import router as financial_router
from app.api.v1.endpoints.pos import router as pos_router
from app.core.config import get_settings
from app.infrastructure.db.database import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager para la aplicación."""
    # Startup
    logger.info("Starting Ω JARBIS Enterprise...")
    
    # Inicializar base de datos (si está habilitada)
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.warning(f"Database initialization skipped: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Ω JARBIS Enterprise...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Sistema de inteligencia operativa para cadenas de restaurantes",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción: especificar dominios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montar directorio estático
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


# ============================================================================
# ENDPOINTS EXISTENTES (legacy compatibility)
# ============================================================================

from pydantic import BaseModel, Field

class EventIn(BaseModel):
    type: str | None = None
    item: str | None = None
    quantity: float = Field(default=0)
    unit: str = Field(default="units")
    source: str = Field(default="chat")
    note: str = Field(default="")


class ConfigIn(BaseModel):
    low_stock_threshold: int = Field(default=10, ge=0)
    anomaly_spike_factor: float = Field(default=1.8, ge=1.0)
    auto_recommendations: bool = True


@app.get("/health")
def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok", "version": settings.APP_VERSION}


@app.get("/config")
def config_panel() -> FileResponse:
    """Panel de configuración (legacy)."""
    return FileResponse(static_dir / "config.html") if (static_dir / "config.html").exists() else {"message": "Config panel not found"}


# ============================================================================
# NUEVOS ENDPOINTS API v1
# ============================================================================

# Mobile Chat (Core Feature)
app.include_router(mobile_chat_router, prefix="/api/v1")

# Recetas
app.include_router(recipes_router, prefix="/api/v1")

# Inventario
app.include_router(inventory_router, prefix="/api/v1")

# Eventos/Cotizaciones
app.include_router(events_router, prefix="/api/v1")

# Finanzas
app.include_router(financial_router, prefix="/api/v1")

# POS Integration
app.include_router(pos_router, prefix="/api/v1")


# ============================================================================
# ROOT ENDPOINT
# ============================================================================

@app.get("/")
def root() -> dict[str, Any]:
    """Root endpoint con información de la API."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": "Sistema de inteligencia operativa para restaurantes",
        "docs": "/docs",
        "endpoints": {
            "mobile_chat": "/api/v1/mobile/chat",
            "recipes": "/api/v1/recipes",
            "inventory": "/api/v1/inventory",
            "events": "/api/v1/events",
            "financial": "/api/v1/financial",
            "pos": "/api/v1/pos",
        },
    }
