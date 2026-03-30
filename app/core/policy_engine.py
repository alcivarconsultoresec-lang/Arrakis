from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from uuid import uuid4

from app.domain.models import Decision, Policy


class PolicyEngine:
    def evaluate(self, policy: Policy | None, *, tenant_id: str, risk: str, recommendation: str, confidence: float) -> Decision:
        mode = policy.mode if policy and policy.active else "suggest"
        action_type = "notify" if mode in {"inform", "suggest"} else "execute"
        result = {
            "inform": "reported",
            "suggest": "pending_confirmation",
            "approval": "awaiting_approval",
            "auto": "executed",
            "auto_reversible": "executed_reversible",
        }[mode]

        return Decision(
            id=str(uuid4()),
            tenant_id=tenant_id,
            detected_risk=risk,
            recommendation=recommendation,
            action_type=action_type,
            confidence=confidence,
            policy_mode=mode,
            approved_by=None,
            executed_at=datetime.now(timezone.utc) if mode in {"auto", "auto_reversible"} else None,
            result=result,
            explanation={
                "why_this_action": recommendation,
                "alternative_evaluated": "manual_review",
                "policy_mode": mode,
            },
        )

    def explain(self, decision: Decision) -> dict:
        return asdict(decision)
