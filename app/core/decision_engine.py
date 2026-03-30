from __future__ import annotations

from app.domain.models import DigitalTwinSnapshot, TenantConfig


class DecisionEngine:
    def detect(self, snapshot: DigitalTwinSnapshot, config: TenantConfig) -> list[dict]:
        findings: list[dict] = []

        for item, qty in snapshot.stock.items():
            if qty <= config.low_stock_threshold:
                findings.append(
                    {
                        "scope": "inventory_restock",
                        "risk": f"Ruptura inminente en {item}",
                        "recommendation": f"Comprar {max(config.low_stock_threshold - qty, 0) + 5:.0f} unidades de {item}",
                        "confidence": 0.82,
                        "evidence": {
                            "stock": qty,
                            "threshold": config.low_stock_threshold,
                            "stockout_probability": snapshot.inferred_state.get("stockout_probability", {}).get(item, 0),
                        },
                    }
                )

        for item, trend in snapshot.consumption_trend.items():
            limit = max(config.low_stock_threshold * config.anomaly_spike_factor, 1)
            if trend >= limit:
                findings.append(
                    {
                        "scope": "consumption_anomaly",
                        "risk": f"Anomalía de consumo en {item}",
                        "recommendation": f"Auditar merma/fraude y revisar proveedor de {item}",
                        "confidence": 0.74,
                        "evidence": {"consumption": trend, "limit": limit},
                    }
                )

        if not findings:
            findings.append(
                {
                    "scope": "stability",
                    "risk": "sin_riesgo_critico",
                    "recommendation": "Operación estable: mantener monitoreo continuo.",
                    "confidence": 0.9,
                    "evidence": {},
                }
            )

        return findings
