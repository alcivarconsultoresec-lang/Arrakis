from __future__ import annotations

from dataclasses import asdict
from typing import Any

from app.core.decision_engine import DecisionEngine
from app.core.mimetic_engine import MimeticEngine
from app.domain.models import TenantConfig
from app.repository.in_memory import InMemoryRepository


class OperationalIntelligenceService:
    def __init__(self) -> None:
        self.repo = InMemoryRepository()
        self.mimetic_engine = MimeticEngine(self.repo)
        self.decision_engine = DecisionEngine()

    def ingest_event(self, tenant_id: str, raw_event: dict[str, Any]) -> dict[str, Any]:
        event = self.mimetic_engine.ingest(tenant_id, raw_event)
        snapshot = self.mimetic_engine.build_snapshot(tenant_id)
        recommendations = self.decision_engine.generate_recommendations(
            snapshot=snapshot,
            config=self.repo.get_config(tenant_id),
        )
        return {
            "event": asdict(event),
            "snapshot": asdict(snapshot),
            "recommendations": recommendations,
        }

    def get_recommendations(self, tenant_id: str) -> dict[str, Any]:
        snapshot = self.mimetic_engine.build_snapshot(tenant_id)
        config = self.repo.get_config(tenant_id)
        recs = self.decision_engine.generate_recommendations(snapshot, config)
        return {
            "snapshot": asdict(snapshot),
            "recommendations": recs,
            "config": asdict(config),
        }

    def set_config(self, tenant_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        config = TenantConfig(
            low_stock_threshold=int(payload.get("low_stock_threshold", 10)),
            anomaly_spike_factor=float(payload.get("anomaly_spike_factor", 1.8)),
            auto_recommendations=bool(payload.get("auto_recommendations", True)),
        )
        self.repo.set_config(tenant_id, config)
        return asdict(config)

    def get_config(self, tenant_id: str) -> dict[str, Any]:
        return asdict(self.repo.get_config(tenant_id))

    def get_audit_trace(self, tenant_id: str) -> dict[str, Any]:
        return self.mimetic_engine.audit_trace(tenant_id)
