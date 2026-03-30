"""Rule Engine determinístico para decisiones operativas."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any


@dataclass
class RuleResult:
    """Resultado de una regla."""
    rule_name: str
    triggered: bool
    message: str
    action: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class RuleEngine:
    """Motor de reglas determinístico para decisiones operativas.
    
    Reglas implementadas:
    - Stock bajo (reabastecimiento)
    - Stock crítico (urgencia)
    - Anomalía de consumo (posible merma/fraude)
    - Caducidad próxima (si aplica)
    - Margen de receta (rentabilidad)
    - Recomendación de compra óptima
    """
    
    def __init__(self) -> None:
        self.rules: list[callable] = [
            self._check_low_stock,
            self._check_critical_stock,
            self._check_consumption_anomaly,
            self._check_recipe_margin,
            self._check_purchase_recommendation,
        ]
    
    def evaluate(self, context: dict[str, Any]) -> list[RuleResult]:
        """Evalúa todas las reglas contra el contexto dado."""
        results: list[RuleResult] = []
        
        for rule in self.rules:
            try:
                result = rule(context)
                if result:
                    results.append(result)
            except Exception as e:
                # Log error pero continuar con otras reglas
                results.append(RuleResult(
                    rule_name=rule.__name__,
                    triggered=False,
                    message=f"Error evaluando regla: {str(e)}",
                ))
        
        return results
    
    def _check_low_stock(self, context: dict[str, Any]) -> RuleResult | None:
        """Verifica stock bajo vs umbral mínimo."""
        inventory = context.get("inventory", [])
        threshold_multiplier = Decimal(str(context.get("low_stock_threshold", 1.0)))
        
        low_items = []
        for item in inventory:
            current = Decimal(str(item.get("current_stock", 0)))
            min_threshold = Decimal(str(item.get("min_stock_threshold", 0))) * threshold_multiplier
            
            if current <= min_threshold and current > 0:
                low_items.append({
                    "name": item.get("name", "unknown"),
                    "current": float(current),
                    "threshold": float(min_threshold),
                    "deficit": float(min_threshold - current),
                })
        
        if low_items:
            return RuleResult(
                rule_name="low_stock_alert",
                triggered=True,
                message=f"{len(low_items)} items con stock bajo detectados",
                action="generate_purchase_order",
                metadata={"items": low_items},
            )
        
        return None
    
    def _check_critical_stock(self, context: dict[str, Any]) -> RuleResult | None:
        """Verifica stock crítico (cercano a cero o negativo)."""
        inventory = context.get("inventory", [])
        
        critical_items = []
        for item in inventory:
            current = Decimal(str(item.get("current_stock", 0)))
            
            if current <= 0:
                critical_items.append({
                    "name": item.get("name", "unknown"),
                    "current": float(current),
                    "severity": "critical" if current < 0 else "out_of_stock",
                })
        
        if critical_items:
            return RuleResult(
                rule_name="critical_stock_alert",
                triggered=True,
                message=f"¡ALERTA! {len(critical_items)} items en stock crítico",
                action="urgent_purchase_order",
                metadata={"items": critical_items, "priority": "high"},
            )
        
        return None
    
    def _check_consumption_anomaly(self, context: dict[str, Any]) -> RuleResult | None:
        """Detecta anomalías en consumo (posible merma o fraude)."""
        consumption_data = context.get("consumption", [])
        anomaly_factor = context.get("anomaly_spike_factor", 2.0)
        
        anomalies = []
        for item in consumption_data:
            current = Decimal(str(item.get("current_consumption", 0)))
            average = Decimal(str(item.get("average_consumption", 0)))
            
            if average > 0 and current >= average * anomaly_factor:
                anomalies.append({
                    "name": item.get("name", "unknown"),
                    "current": float(current),
                    "average": float(average),
                    "ratio": float(current / average) if average > 0 else 0,
                })
        
        if anomalies:
            return RuleResult(
                rule_name="consumption_anomaly",
                triggered=True,
                message=f"{len(anomalies)} anomalías de consumo detectadas - validar merma/fraude",
                action="investigate_waste",
                metadata={"items": anomalies, "priority": "medium"},
            )
        
        return None
    
    def _check_recipe_margin(self, context: dict[str, Any]) -> RuleResult | None:
        """Verifica márgenes de recetas vs objetivo."""
        recipes = context.get("recipes", [])
        
        low_margin_recipes = []
        for recipe in recipes:
            cost = Decimal(str(recipe.get("total_cost", 0)))
            price = Decimal(str(recipe.get("selling_price", 0)))
            target_margin = Decimal(str(recipe.get("target_margin", 30)))
            
            if price > 0 and cost > 0:
                actual_margin = ((price - cost) / price) * 100
                
                if actual_margin < target_margin:
                    low_margin_recipes.append({
                        "name": recipe.get("name", "unknown"),
                        "cost": float(cost),
                        "price": float(price),
                        "actual_margin": float(actual_margin),
                        "target_margin": float(target_margin),
                        "suggested_price": float(cost / (1 - target_margin / 100)) if target_margin < 100 else 0,
                    })
        
        if low_margin_recipes:
            return RuleResult(
                rule_name="low_recipe_margin",
                triggered=True,
                message=f"{len(low_margin_recipes)} recetas con margen por debajo del objetivo",
                action="review_pricing",
                metadata={"recipes": low_margin_recipes},
            )
        
        return None
    
    def _check_purchase_recommendation(self, context: dict[str, Any]) -> RuleResult | None:
        """Genera recomendación de compra óptima basada en consumo y stock."""
        inventory = context.get("inventory", [])
        consumption = context.get("consumption", [])
        days_horizon = context.get("planning_horizon_days", 7)
        
        recommendations = []
        consumption_map = {item.get("name"): item for item in consumption}
        
        for item in inventory:
            name = item.get("name", "unknown")
            current = Decimal(str(item.get("current_stock", 0)))
            max_threshold = Decimal(str(item.get("max_stock_threshold", 0)))
            
            # Obtener consumo promedio diario
            cons_data = consumption_map.get(name, {})
            avg_daily = Decimal(str(cons_data.get("average_daily_consumption", 0)))
            
            if avg_daily > 0:
                projected_consumption = avg_daily * days_horizon
                optimal_stock = projected_consumption * 1.2  # 20% buffer
                
                if current < optimal_stock and current > 0:
                    recommended_qty = min(optimal_stock - current, max_threshold - current) if max_threshold > 0 else optimal_stock - current
                    
                    if recommended_qty > 0:
                        recommendations.append({
                            "name": name,
                            "current_stock": float(current),
                            "recommended_qty": float(recommended_qty),
                            "unit": item.get("unit", "units"),
                            "reason": f"Proyección {days_horizon} días: {float(projected_consumption):.2f}",
                        })
        
        if recommendations:
            return RuleResult(
                rule_name="purchase_recommendation",
                triggered=True,
                message=f"{len(recommendations)} recomendaciones de compra generadas",
                action="create_purchase_suggestions",
                metadata={"recommendations": recommendations},
            )
        
        return None


# Instancia global
rule_engine = RuleEngine()
