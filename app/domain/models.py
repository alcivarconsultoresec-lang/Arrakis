from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal

PolicyMode = Literal["inform", "suggest", "approval", "auto", "auto_reversible"]


@dataclass(slots=True)
class Event:
    id: str
    tenant_id: str
    type: str
    raw_payload: dict[str, Any]
    normalized_payload: dict[str, Any]
    confidence_score: float
    source: str
    correlation_id: str
    causation_id: str | None
    timestamp: datetime


@dataclass(slots=True)
class Entity:
    id: str
    tenant_id: str
    name: str
    type: str
    aliases: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    state: str = "active"


@dataclass(slots=True)
class Policy:
    id: str
    tenant_id: str
    scope: str
    mode: PolicyMode
    thresholds: dict[str, float] = field(default_factory=dict)
    active: bool = True


@dataclass(slots=True)
class Decision:
    id: str
    tenant_id: str
    detected_risk: str
    recommendation: str
    action_type: str
    confidence: float
    policy_mode: PolicyMode
    approved_by: str | None
    executed_at: datetime | None
    result: str
    explanation: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class TenantConfig:
    low_stock_threshold: int = 10
    anomaly_spike_factor: float = 1.8
    auto_recommendations: bool = True
    default_policy_mode: PolicyMode = "suggest"


@dataclass(slots=True)
class DigitalTwinSnapshot:
    tenant_id: str
    stock: dict[str, float]
    consumption_trend: dict[str, float]
    inferred_state: dict[str, Any]
    simulated_state: dict[str, Any]
    risks: list[str]
    generated_at: datetime
