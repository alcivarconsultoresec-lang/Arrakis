"""IA forecasting para casos complejos (opcional)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any


@dataclass
class ForecastResult:
    """Resultado de forecast."""
    item_name: str
    predicted_demand: float
    confidence: float  # 0-1
    prediction_date: datetime
    factors: list[str]


class ForecastEngine:
    """Motor de forecasting con IA (simplificado para MVP).
    
    En producción, esto usaría:
    - Modelos de series temporales (Prophet, ARIMA)
    - Features externos (clima, eventos locales, día de semana)
    - Aprendizaje continuo
    
    Para MVP: usa promedio móvil simple con ajustes estacionales básicos.
    """
    
    def __init__(self) -> None:
        self.enabled = False  # Se activa solo si hay datos suficientes
    
    def predict_demand(
        self,
        historical_data: list[dict[str, Any]],
        days_ahead: int = 7,
        item_name: str = "unknown",
    ) -> list[ForecastResult]:
        """Predice demanda para los próximos días.
        
        Args:
            historical_data: Lista de {date, quantity} históricos
            days_ahead: Días a predecir
            item_name: Nombre del item
        
        Returns:
            Lista de ForecastResult por día
        """
        if not historical_data or len(historical_data) < 7:
            # No hay suficientes datos para forecast confiable
            self.enabled = False
            return []
        
        self.enabled = True
        
        # Calcular promedio móvil semanal
        daily_totals: dict[int, float] = {}  # day_of_week -> total
        for record in historical_data:
            date = record.get("date")
            if isinstance(date, str):
                date = datetime.fromisoformat(date.replace("Z", "+00:00"))
            if date:
                dow = date.weekday()
                qty = float(record.get("quantity", 0))
                daily_totals[dow] = daily_totals.get(dow, 0) + qty
        
        # Promedio por día de semana
        avg_by_dow = {dow: total / max(1, len(historical_data) // 7) 
                      for dow, total in daily_totals.items()}
        
        # Generar predicciones
        results = []
        today = datetime.now(timezone.utc)
        
        for i in range(days_ahead):
            pred_date = today + timedelta(days=i)
            dow = pred_date.weekday()
            
            # Usar promedio del día de semana correspondiente
            base_prediction = avg_by_dow.get(dow, sum(avg_by_dow.values()) / max(1, len(avg_by_dow)))
            
            # Ajuste por tendencia reciente (últimos 3 días)
            recent_records = sorted(historical_data, key=lambda x: x.get("date", ""), reverse=True)[:3]
            if recent_records:
                recent_avg = sum(float(r.get("quantity", 0)) for r in recent_records) / len(recent_records)
                trend_factor = recent_avg / max(0.1, base_prediction) if base_prediction > 0 else 1
                base_prediction *= min(1.3, max(0.7, trend_factor))
            
            # Confidence basado en cantidad de datos
            confidence = min(0.95, 0.5 + (len(historical_data) / 100))
            
            results.append(ForecastResult(
                item_name=item_name,
                predicted_demand=round(base_prediction, 2),
                confidence=round(confidence, 2),
                prediction_date=pred_date,
                factors=["historical_average", "day_of_week", "recent_trend"],
            ))
        
        return results
    
    def detect_waste_anomaly(
        self,
        waste_history: list[dict[str, Any]],
        threshold_std: float = 2.0,
    ) -> list[dict[str, Any]]:
        """Detecta anomalías en historial de merma.
        
        Args:
            waste_history: Lista de {date, quantity} de merma histórica
            threshold_std: Número de desviaciones estándar para considerar anomalía
        
        Returns:
            Lista de anomalías detectadas
        """
        if len(waste_history) < 10:
            return []
        
        quantities = [float(w.get("quantity", 0)) for w in waste_history]
        
        # Calcular media y desviación estándar
        mean = sum(quantities) / len(quantities)
        variance = sum((q - mean) ** 2 for q in quantities) / len(quantities)
        std_dev = variance ** 0.5
        
        if std_dev == 0:
            return []
        
        anomalies = []
        for record in waste_history:
            qty = float(record.get("quantity", 0))
            z_score = (qty - mean) / std_dev
            
            if abs(z_score) > threshold_std:
                anomalies.append({
                    "date": record.get("date"),
                    "quantity": qty,
                    "z_score": round(z_score, 2),
                    "severity": "high" if abs(z_score) > 3 else "medium",
                    "expected_range": f"{mean - std_dev:.2f} - {mean + std_dev:.2f}",
                })
        
        return anomalies
    
    def optimize_price(
        self,
        cost: float,
        target_margin: float,
        competitor_prices: list[float] | None = None,
        demand_elasticity: float = -1.5,
    ) -> dict[str, Any]:
        """Optimiza precio basado en margen objetivo y competencia.
        
        Args:
            cost: Costo del producto
            target_margin: Margen objetivo (%)
            competitor_prices: Precios de competencia (opcional)
            demand_elasticity: Elasticidad precio de la demanda
        
        Returns:
            Dict con precio recomendado y análisis
        """
        # Precio mínimo para margen objetivo
        min_price = cost / (1 - target_margin / 100) if target_margin < 100 else cost * 2
        
        # Si hay competencia, ajustar estrategia
        if competitor_prices:
            avg_competitor = sum(competitor_prices) / len(competitor_prices)
            
            # Estrategia: precio competitivo pero con margen aceptable
            if min_price > avg_competitor * 1.1:
                # No podemos competir en precio, destacar calidad
                recommended_price = min_price
                strategy = "premium"
            elif min_price < avg_competitor * 0.9:
                # Podemos undercutear y mantener margen
                recommended_price = avg_competitor * 0.95
                strategy = "competitive"
            else:
                # Precio similar a competencia
                recommended_price = avg_competitor
                strategy = "match"
        else:
            recommended_price = min_price
            strategy = "cost_plus"
        
        projected_margin = ((recommended_price - cost) / recommended_price) * 100 if recommended_price > 0 else 0
        
        return {
            "recommended_price": round(recommended_price, 2),
            "minimum_price": round(min_price, 2),
            "projected_margin": round(projected_margin, 2),
            "strategy": strategy,
            "cost": cost,
        }


# Instancia global
forecast_engine = ForecastEngine()
