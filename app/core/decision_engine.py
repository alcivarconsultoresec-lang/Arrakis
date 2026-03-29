from __future__ import annotations

from app.domain.models import DigitalTwinSnapshot, TenantConfig


class DecisionEngine:
    def generate_recommendations(
        self,
        snapshot: DigitalTwinSnapshot,
        config: TenantConfig,
    ) -> list[str]:
        recommendations: list[str] = []

        for item, qty in snapshot.stock.items():
            if qty <= config.low_stock_threshold:
                recommendations.append(
                    f"Reabastecer {item}: stock actual {qty:.2f} <= umbral {config.low_stock_threshold}."
                )

        for item, trend in snapshot.consumption_trend.items():
            if trend >= max(config.low_stock_threshold * config.anomaly_spike_factor, 1):
                recommendations.append(
                    f"Anomalía potencial en {item}: consumo acumulado {trend:.2f}; validar merma/fraude."
                )

        if snapshot.risks:
            recommendations.extend([f"Riesgo detectado: {risk}" for risk in snapshot.risks])

        if not recommendations:
            recommendations.append("Operación estable: no se requieren acciones inmediatas.")

        return recommendations
