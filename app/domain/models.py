from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class Event:
    id: str
    tenant_id: str
    type: str
    payload: dict[str, Any]
    timestamp: datetime


@dataclass(slots=True)
class Entity:
    id: str
    tenant_id: str
    name: str
    type: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class TenantConfig:
    low_stock_threshold: int = 10
    anomaly_spike_factor: float = 1.8
    auto_recommendations: bool = True


@dataclass(slots=True)
class DigitalTwinSnapshot:
    tenant_id: str
    stock: dict[str, float]
    consumption_trend: dict[str, float]
    risks: list[str]
    generated_at: datetime
