from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.services.operational_service import OperationalIntelligenceService

app = FastAPI(title="Ω JARBIS", version="0.2.0")
service = OperationalIntelligenceService()

static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")


class EventIn(BaseModel):
    type: str | None = None
    item: str | None = None
    quantity: float = Field(default=0)
    unit: str = Field(default="units")
    source: str = Field(default="chat")
    note: str = Field(default="")
    correlation_id: str | None = None
    causation_id: str | None = None


class ConfigIn(BaseModel):
    low_stock_threshold: int = Field(default=10, ge=0)
    anomaly_spike_factor: float = Field(default=1.8, ge=1.0)
    auto_recommendations: bool = True
    default_policy_mode: Literal["inform", "suggest", "approval", "auto", "auto_reversible"] = "suggest"


class PolicyIn(BaseModel):
    scope: str
    mode: Literal["inform", "suggest", "approval", "auto", "auto_reversible"] = "suggest"
    thresholds: dict[str, float] = Field(default_factory=dict)
    active: bool = True


class SimulationIn(BaseModel):
    item: str
    buy_quantity: float = Field(gt=0)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/config")
def config_panel() -> FileResponse:
    return FileResponse(static_dir / "config.html")


@app.post("/api/v1/tenants/{tenant_id}/events")
def ingest_event(tenant_id: str, payload: EventIn) -> dict[str, Any]:
    return service.ingest_event(tenant_id, payload.model_dump(exclude_none=True))


@app.get("/api/v1/tenants/{tenant_id}/recommendations")
def get_recommendations(tenant_id: str) -> dict[str, Any]:
    return service.get_recommendations(tenant_id)


@app.get("/api/v1/tenants/{tenant_id}/config")
def get_config(tenant_id: str) -> dict[str, Any]:
    return service.get_config(tenant_id)


@app.put("/api/v1/tenants/{tenant_id}/config")
def update_config(tenant_id: str, payload: ConfigIn) -> dict[str, Any]:
    return service.set_config(tenant_id, payload.model_dump())


@app.put("/api/v1/tenants/{tenant_id}/policies")
def upsert_policy(tenant_id: str, payload: PolicyIn) -> dict[str, Any]:
    return service.upsert_policy(tenant_id, payload.model_dump())


@app.get("/api/v1/tenants/{tenant_id}/policies")
def list_policies(tenant_id: str) -> list[dict[str, Any]]:
    return service.list_policies(tenant_id)


@app.post("/api/v1/tenants/{tenant_id}/simulate")
def simulate(tenant_id: str, payload: SimulationIn) -> dict[str, Any]:
    return service.simulate(tenant_id, payload.item, payload.buy_quantity)


@app.get("/api/v1/tenants/{tenant_id}/control-tower")
def control_tower(tenant_id: str) -> dict[str, Any]:
    return service.control_tower(tenant_id)


@app.get("/api/v1/tenants/{tenant_id}/audit")
def get_audit_trace(tenant_id: str) -> dict[str, Any]:
    return service.get_audit_trace(tenant_id)
