from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.domain.models import DigitalTwinSnapshot, Entity, Event
from app.repository.in_memory import InMemoryRepository


class MimeticEngine:
    """Cognitive core: semantic normalization + dynamic business modeling."""

    SUPPORTED_EVENT_TYPES = {"purchase", "sale", "waste", "consumption", "adjustment"}

    def __init__(self, repo: InMemoryRepository) -> None:
        self.repo = repo
        self._stock: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
        self._consumption: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))

    def ingest(self, tenant_id: str, raw_event: dict[str, Any]) -> Event:
        event_type, confidence = self._classify_event(raw_event)
        item = self._extract_item(raw_event)
        quantity = float(raw_event.get("quantity", 0) or 0)
        source = str(raw_event.get("source", "chat"))

        entity = self._ensure_entity(tenant_id=tenant_id, name=item, entity_type="inventory_item")
        normalized_payload = {
            "item": entity.name,
            "entity_id": entity.id,
            "quantity": quantity,
            "unit": raw_event.get("unit", "units"),
            "semantic_tags": self._semantic_tags(event_type),
            "note": raw_event.get("note", ""),
        }
        event = Event(
            id=str(uuid4()),
            tenant_id=tenant_id,
            type=event_type,
            raw_payload=raw_event,
            normalized_payload=normalized_payload,
            confidence_score=confidence,
            source=source,
            correlation_id=str(raw_event.get("correlation_id", uuid4())),
            causation_id=raw_event.get("causation_id"),
            timestamp=datetime.now(timezone.utc),
        )

        self.repo.append_event(event)
        self._apply_to_twin(event)
        return event

    def build_snapshot(self, tenant_id: str) -> DigitalTwinSnapshot:
        risks: list[str] = []
        inferred: dict[str, Any] = {"stockout_probability": {}}
        simulated: dict[str, Any] = {"buy_now_impact": {}}

        for item, qty in self._stock[tenant_id].items():
            if qty < 0:
                risks.append(f"Stock inconsistente para {item}: {qty:.2f}")
            consumption = self._consumption[tenant_id].get(item, 0)
            probability = min(0.99, consumption / (qty + consumption + 1))
            inferred["stockout_probability"][item] = round(probability, 2)
            simulated["buy_now_impact"][item] = {"if_buy_10": round(qty + 10, 2)}

        return DigitalTwinSnapshot(
            tenant_id=tenant_id,
            stock=dict(self._stock[tenant_id]),
            consumption_trend=dict(self._consumption[tenant_id]),
            inferred_state=inferred,
            simulated_state=simulated,
            risks=risks,
            generated_at=datetime.now(timezone.utc),
        )

    def _classify_event(self, raw_event: dict[str, Any]) -> tuple[str, float]:
        explicit_type = str(raw_event.get("type", "")).strip().lower()
        if explicit_type in self.SUPPORTED_EVENT_TYPES:
            return explicit_type, 0.95

        note = str(raw_event.get("note", "")).lower()
        mapping = {
            "purchase": ["compr", "buy", "purchase"],
            "sale": ["vend", "sale"],
            "waste": ["dañ", "merma", "waste"],
            "consumption": ["consum", "use"],
        }
        for kind, tokens in mapping.items():
            if any(token in note for token in tokens):
                return kind, 0.75
        return "adjustment", 0.5

    def _extract_item(self, raw_event: dict[str, Any]) -> str:
        item = str(raw_event.get("item", "")).strip()
        if item:
            return item.lower()
        note = str(raw_event.get("note", "")).strip().lower()
        return note.split()[-1] if note else "unknown-item"

    def _semantic_tags(self, event_type: str) -> list[str]:
        return ["inventory", event_type, "operational_event"]

    def _ensure_entity(self, tenant_id: str, name: str, entity_type: str) -> Entity:
        entity_id = f"{entity_type}:{name}"
        current = {e.id: e for e in self.repo.list_entities(tenant_id)}
        if entity_id in current:
            return current[entity_id]

        entity = Entity(id=entity_id, tenant_id=tenant_id, name=name, type=entity_type, aliases=[name])
        self.repo.upsert_entity(entity)
        return entity

    def _apply_to_twin(self, event: Event) -> None:
        item = event.normalized_payload["item"]
        quantity = float(event.normalized_payload["quantity"])
        if event.type == "purchase":
            self._stock[event.tenant_id][item] += quantity
        elif event.type in {"sale", "waste", "consumption"}:
            self._stock[event.tenant_id][item] -= quantity
            self._consumption[event.tenant_id][item] += quantity
        else:
            self._stock[event.tenant_id][item] += quantity

    def audit_trace(self, tenant_id: str) -> dict[str, Any]:
        snapshot = self.build_snapshot(tenant_id)
        return {
            "tenant_id": tenant_id,
            "stock": snapshot.stock,
            "consumption": snapshot.consumption_trend,
            "inferred_state": snapshot.inferred_state,
            "simulated_state": snapshot.simulated_state,
            "risks": snapshot.risks,
            "events": [asdict(evt) for evt in self.repo.list_events(tenant_id)],
            "entities": [asdict(ent) for ent in self.repo.list_entities(tenant_id)],
            "generated_at": snapshot.generated_at.isoformat(),
        }
