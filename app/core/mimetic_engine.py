from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.domain.models import DigitalTwinSnapshot, Entity, Event
from app.repository.in_memory import InMemoryRepository


class MimeticEngine:
    """Core adaptive engine.

    Responsibilities:
    - normalize natural language/structured payloads into canonical events
    - create dynamic entities as the business vocabulary evolves
    - maintain a continuously updated digital twin state per tenant
    """

    SUPPORTED_EVENT_TYPES = {"purchase", "sale", "waste", "consumption", "adjustment"}

    def __init__(self, repo: InMemoryRepository) -> None:
        self.repo = repo
        self._stock: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
        self._consumption: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))

    def ingest(self, tenant_id: str, raw_event: dict[str, Any]) -> Event:
        event_type = self._classify_event(raw_event)
        item = self._extract_item(raw_event)
        quantity = float(raw_event.get("quantity", 0) or 0)

        entity = self._ensure_entity(tenant_id=tenant_id, name=item, entity_type="inventory_item")

        normalized_payload = {
            "item": entity.name,
            "entity_id": entity.id,
            "quantity": quantity,
            "unit": raw_event.get("unit", "units"),
            "source": raw_event.get("source", "chat"),
            "note": raw_event.get("note", ""),
        }
        event = Event(
            id=str(uuid4()),
            tenant_id=tenant_id,
            type=event_type,
            payload=normalized_payload,
            timestamp=datetime.now(timezone.utc),
        )

        self.repo.append_event(event)
        self._apply_to_twin(event)
        return event

    def build_snapshot(self, tenant_id: str) -> DigitalTwinSnapshot:
        risks: list[str] = []
        for item, qty in self._stock[tenant_id].items():
            if qty < 0:
                risks.append(f"Stock inconsistente para {item}: {qty:.2f}")

        return DigitalTwinSnapshot(
            tenant_id=tenant_id,
            stock=dict(self._stock[tenant_id]),
            consumption_trend=dict(self._consumption[tenant_id]),
            risks=risks,
            generated_at=datetime.now(timezone.utc),
        )

    def _classify_event(self, raw_event: dict[str, Any]) -> str:
        explicit_type = str(raw_event.get("type", "")).strip().lower()
        if explicit_type in self.SUPPORTED_EVENT_TYPES:
            return explicit_type

        note = str(raw_event.get("note", "")).lower()
        if any(token in note for token in ["compr", "buy", "purchase"]):
            return "purchase"
        if any(token in note for token in ["vend", "sale"]):
            return "sale"
        if any(token in note for token in ["dañ", "merma", "waste"]):
            return "waste"
        if any(token in note for token in ["consum", "use"]):
            return "consumption"
        return "adjustment"

    def _extract_item(self, raw_event: dict[str, Any]) -> str:
        item = str(raw_event.get("item", "")).strip()
        if item:
            return item.lower()

        note = str(raw_event.get("note", "")).strip().lower()
        return note.split()[-1] if note else "unknown-item"

    def _ensure_entity(self, tenant_id: str, name: str, entity_type: str) -> Entity:
        entity_id = f"{entity_type}:{name}"
        current = {e.id: e for e in self.repo.list_entities(tenant_id)}
        if entity_id in current:
            return current[entity_id]

        entity = Entity(id=entity_id, tenant_id=tenant_id, name=name, type=entity_type)
        self.repo.upsert_entity(entity)
        return entity

    def _apply_to_twin(self, event: Event) -> None:
        item = event.payload["item"]
        quantity = float(event.payload["quantity"])

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
            "risks": snapshot.risks,
            "events": [asdict(evt) for evt in self.repo.list_events(tenant_id)],
            "entities": [asdict(ent) for ent in self.repo.list_entities(tenant_id)],
            "generated_at": snapshot.generated_at.isoformat(),
        }
