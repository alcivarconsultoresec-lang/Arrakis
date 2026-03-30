from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.core.decision_engine import DecisionEngine
from app.core.event_bus import InMemoryEventBus
from app.core.mimetic_engine import MimeticEngine
from app.core.policy_engine import PolicyEngine
from app.domain.models import Policy, TenantConfig
from app.repository.in_memory import InMemoryRepository


class OperationalIntelligenceService:
    def __init__(self) -> None:
        self.repo = InMemoryRepository()
        self.bus = InMemoryEventBus()
        self.mimetic_engine = MimeticEngine(self.repo)
        self.decision_engine = DecisionEngine()
        self.policy_engine = PolicyEngine()

    def ingest_event(self, tenant_id: str, raw_event: dict[str, Any]) -> dict[str, Any]:
        self.bus.publish("ingestion.events", {"tenant_id": tenant_id, "event": raw_event}, priority=3)
        event = self.mimetic_engine.ingest(tenant_id, raw_event)
        snapshot = self.mimetic_engine.build_snapshot(tenant_id)

        findings = self.decision_engine.detect(snapshot=snapshot, config=self.repo.get_config(tenant_id))
        decisions = []
        for finding in findings:
            policy = self.repo.get_policy(tenant_id, finding["scope"])
            decision = self.policy_engine.evaluate(
                policy,
                tenant_id=tenant_id,
                risk=finding["risk"],
                recommendation=finding["recommendation"],
                confidence=finding["confidence"],
            )
            decision.explanation.update(
                {
                    "event_id": event.id,
                    "evidence": finding["evidence"],
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )
            self.repo.append_decision(decision)
            decisions.append(asdict(decision))

        return {
            "event": asdict(event),
            "snapshot": asdict(snapshot),
            "decisions": decisions,
        }

    def get_recommendations(self, tenant_id: str) -> dict[str, Any]:
        snapshot = self.mimetic_engine.build_snapshot(tenant_id)
        findings = self.decision_engine.detect(snapshot, self.repo.get_config(tenant_id))
        return {
            "snapshot": asdict(snapshot),
            "findings": findings,
            "config": asdict(self.repo.get_config(tenant_id)),
        }

    def set_config(self, tenant_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        config = TenantConfig(
            low_stock_threshold=int(payload.get("low_stock_threshold", 10)),
            anomaly_spike_factor=float(payload.get("anomaly_spike_factor", 1.8)),
            auto_recommendations=bool(payload.get("auto_recommendations", True)),
            default_policy_mode=payload.get("default_policy_mode", "suggest"),
        )
        self.repo.set_config(tenant_id, config)
        return asdict(config)

    def get_config(self, tenant_id: str) -> dict[str, Any]:
        return asdict(self.repo.get_config(tenant_id))

    def upsert_policy(self, tenant_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        policy = Policy(
            id=payload.get("id", str(uuid4())),
            tenant_id=tenant_id,
            scope=payload["scope"],
            mode=payload.get("mode", "suggest"),
            thresholds=payload.get("thresholds", {}),
            active=bool(payload.get("active", True)),
        )
        self.repo.upsert_policy(policy)
        return asdict(policy)

    def list_policies(self, tenant_id: str) -> list[dict[str, Any]]:
        return [asdict(pol) for pol in self.repo.list_policies(tenant_id)]

    def get_audit_trace(self, tenant_id: str) -> dict[str, Any]:
        trace = self.mimetic_engine.audit_trace(tenant_id)
        trace["decisions"] = [asdict(dec) for dec in self.repo.list_decisions(tenant_id)]
        trace["policies"] = [asdict(pol) for pol in self.repo.list_policies(tenant_id)]
        trace["dlq"] = [asdict(msg) for msg in self.bus.get_dlq()]
        return trace

    def simulate(self, tenant_id: str, item: str, buy_quantity: float) -> dict[str, Any]:
        snapshot = self.mimetic_engine.build_snapshot(tenant_id)
        current_stock = snapshot.stock.get(item, 0.0)
        projected = current_stock + buy_quantity
        return {
            "tenant_id": tenant_id,
            "item": item,
            "current_stock": current_stock,
            "buy_quantity": buy_quantity,
            "projected_stock": projected,
            "impact": "reduce_stockout_risk" if projected > current_stock else "no_change",
        }

    def control_tower(self, tenant_id: str) -> dict[str, Any]:
        snapshot = self.mimetic_engine.build_snapshot(tenant_id)
        decisions = self.repo.list_decisions(tenant_id)
        return {
            "tenant_id": tenant_id,
            "operational_health": "stable" if not snapshot.risks else "attention_required",
            "risk_map": snapshot.risks,
            "pending_decisions": [asdict(d) for d in decisions if d.result in {"pending_confirmation", "awaiting_approval"}],
            "executed_decisions": [asdict(d) for d in decisions if d.result in {"executed", "executed_reversible"}],
            "kpis": {
                "events": len(self.repo.list_events(tenant_id)),
                "entities": len(self.repo.list_entities(tenant_id)),
                "decisions": len(decisions),
            },
        }
