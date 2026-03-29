from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict
from typing import Any

from app.domain.models import Entity, Event, TenantConfig


class InMemoryRepository:
    def __init__(self) -> None:
        self._events: dict[str, list[Event]] = defaultdict(list)
        self._entities: dict[str, dict[str, Entity]] = defaultdict(dict)
        self._config: dict[str, TenantConfig] = defaultdict(TenantConfig)

    def append_event(self, event: Event) -> None:
        self._events[event.tenant_id].append(event)

    def list_events(self, tenant_id: str) -> list[Event]:
        return list(self._events[tenant_id])

    def upsert_entity(self, entity: Entity) -> None:
        self._entities[entity.tenant_id][entity.id] = entity

    def list_entities(self, tenant_id: str) -> list[Entity]:
        return list(self._entities[tenant_id].values())

    def set_config(self, tenant_id: str, config: TenantConfig) -> None:
        self._config[tenant_id] = config

    def get_config(self, tenant_id: str) -> TenantConfig:
        return self._config[tenant_id]

    def export_tenant_state(self, tenant_id: str) -> dict[str, Any]:
        return {
            "events": [asdict(evt) for evt in self._events[tenant_id]],
            "entities": [asdict(ent) for ent in self._entities[tenant_id].values()],
            "config": asdict(self._config[tenant_id]),
        }
