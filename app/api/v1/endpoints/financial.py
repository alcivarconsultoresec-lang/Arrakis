"""Endpoints para reportes financieros."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/financial", tags=["financial"])


# ============================================================================
# SCHEMAS
# ============================================================================

class FinancialDashboard(BaseModel):
    """Dashboard financiero resumen."""
    period: str
    revenue: float
    costs: float
    expenses: float
    waste_cost: float
    gross_profit: float
    net_profit: float
    margin_percent: float
    profit_margin_percent: float
    trends: dict[str, Any]
    top_categories: list[dict]
    alerts: list[str]


class FinancialRecordCreate(BaseModel):
    """Crear registro financiero."""
    record_type: str  # revenue, cost, expense, waste
    category: str  # food, labor, overhead, etc.
    amount: float
    date: datetime | None = None
    description: str | None = None
    location_id: str | None = None


class PeriodRequest(BaseModel):
    """Solicitud de período."""
    start_date: datetime
    end_date: datetime
    group_by: str = "day"  # day, week, month


# ============================================================================
# MOCK DATA
# ============================================================================

FINANCIAL_RECORDS_DB: list[dict] = [
    # Ingresos (últimos 30 días simulados)
    {"id": "fr-1", "type": "revenue", "category": "food_sales", "amount": 15000, "date": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(), "description": "Ventas del día"},
    {"id": "fr-2", "type": "revenue", "category": "beverage_sales", "amount": 5000, "date": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(), "description": "Bebidas del día"},
    {"id": "fr-3", "type": "revenue", "category": "food_sales", "amount": 18000, "date": (datetime.now(timezone.utc) - timedelta(days=2)).isoformat(), "description": "Ventas del día"},
    {"id": "fr-4", "type": "revenue", "category": "beverage_sales", "amount": 6000, "date": (datetime.now(timezone.utc) - timedelta(days=2)).isoformat(), "description": "Bebidas del día"},
    {"id": "fr-5", "type": "revenue", "category": "event_catering", "amount": 25000, "date": (datetime.now(timezone.utc) - timedelta(days=3)).isoformat(), "description": "Evento corporativo"},
    
    # Costos
    {"id": "fr-6", "type": "cost", "category": "food_cost", "amount": 8000, "date": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(), "description": "Compra de ingredientes"},
    {"id": "fr-7", "type": "cost", "category": "beverage_cost", "amount": 2000, "date": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(), "description": "Compra de bebidas"},
    {"id": "fr-8", "type": "cost", "category": "food_cost", "amount": 9500, "date": (datetime.now(timezone.utc) - timedelta(days=2)).isoformat(), "description": "Compra de ingredientes"},
    
    # Gastos operativos
    {"id": "fr-9", "type": "expense", "category": "labor", "amount": 12000, "date": (datetime.now(timezone.utc) - timedelta(days=0)).isoformat(), "description": "Nómina quincenal"},
    {"id": "fr-10", "type": "expense", "category": "rent", "amount": 8000, "date": (datetime.now(timezone.utc) - timedelta(days=0)).isoformat(), "description": "Renta del local"},
    {"id": "fr-11", "type": "expense", "category": "utilities", "amount": 2500, "date": (datetime.now(timezone.utc) - timedelta(days=5)).isoformat(), "description": "Servicios públicos"},
    
    # Mermas
    {"id": "fr-12", "type": "waste", "category": "food_waste", "amount": 800, "date": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(), "description": "Merma de verduras"},
    {"id": "fr-13", "type": "waste", "category": "food_waste", "amount": 1200, "date": (datetime.now(timezone.utc) - timedelta(days=4)).isoformat(), "description": "Producto caducado"},
]


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def parse_date(date_str: str) -> datetime:
    """Parsea string de fecha a datetime."""
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except:
        return datetime.now(timezone.utc)


def calculate_financial_metrics(
    records: list[dict],
    start_date: datetime,
    end_date: datetime,
) -> dict[str, Any]:
    """Calcula métricas financieras para un período."""
    
    # Filtrar por período
    filtered = []
    for r in records:
        record_date = parse_date(r["date"])
        if start_date <= record_date <= end_date:
            filtered.append(r)
    
    # Calcular totales por tipo
    revenue = sum(r["amount"] for r in filtered if r["type"] == "revenue")
    costs = sum(r["amount"] for r in filtered if r["type"] == "cost")
    expenses = sum(r["amount"] for r in filtered if r["type"] == "expense")
    waste = sum(r["amount"] for r in filtered if r["type"] == "waste")
    
    # Calcular ganancias
    gross_profit = revenue - costs
    net_profit = gross_profit - expenses - waste
    
    # Márgenes
    margin_percent = ((gross_profit / revenue) * 100) if revenue > 0 else 0
    profit_margin_percent = ((net_profit / revenue) * 100) if revenue > 0 else 0
    
    # Agrupar por categoría
    by_category: dict[str, float] = {}
    for r in filtered:
        cat = r["category"]
        by_category[cat] = by_category.get(cat, 0) + r["amount"]
    
    # Top categorías
    top_categories = sorted(
        [{"category": k, "amount": v} for k, v in by_category.items()],
        key=lambda x: x["amount"],
        reverse=True
    )[:5]
    
    # Tendencias (simplificado: comparación con período anterior)
    prev_start = start_date - (end_date - start_date)
    prev_end = start_date - timedelta(days=1)
    
    prev_revenue = sum(
        r["amount"] for r in records
        if r["type"] == "revenue" and prev_start <= parse_date(r["date"]) <= prev_end
    )
    
    revenue_trend = ((revenue - prev_revenue) / prev_revenue * 100) if prev_revenue > 0 else 0
    
    trends = {
        "revenue_change_percent": round(revenue_trend, 2),
        "revenue_direction": "up" if revenue_trend > 0 else "down" if revenue_trend < 0 else "stable",
    }
    
    # Alertas
    alerts = []
    if waste > revenue * 0.05:
        alerts.append(f"⚠️ Merma alta: {waste:.2f} ({waste/revenue*100:.1f}% de ingresos)")
    if margin_percent < 25:
        alerts.append(f"⚠️ Margen bruto bajo: {margin_percent:.1f}% (objetivo: 30%+)")
    if profit_margin_percent < 10:
        alerts.append(f"⚠️ Margen neto bajo: {profit_margin_percent:.1f}% (objetivo: 15%+)")
    if costs > revenue * 0.4:
        alerts.append(f"⚠️ Costos de comida altos: {costs/revenue*100:.1f}% (objetivo: <35%)")
    
    return {
        "revenue": round(revenue, 2),
        "costs": round(costs, 2),
        "expenses": round(expenses, 2),
        "waste_cost": round(waste, 2),
        "gross_profit": round(gross_profit, 2),
        "net_profit": round(net_profit, 2),
        "margin_percent": round(margin_percent, 2),
        "profit_margin_percent": round(profit_margin_percent, 2),
        "trends": trends,
        "top_categories": top_categories,
        "alerts": alerts,
        "record_count": len(filtered),
    }


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("/dashboard", response_model=FinancialDashboard, summary="Dashboard financiero")
async def get_financial_dashboard(
    period: str = "month",  # day, week, month, year, custom
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> FinancialDashboard:
    """
    **Dashboard financiero completo.**
    
    Proporciona visión general de la salud financiera:
    - Ingresos totales y por categoría
    - Costos de comida/bebida
    - Gastos operativos
    - Mermas y su impacto
    - Márgenes (bruto y neto)
    - Tendencias vs período anterior
    - Alertas automáticas
    
    Períodos predefinidos: hoy, semana, mes, año
    O período personalizado con fechas específicas.
    """
    now = datetime.now(timezone.utc)
    
    # Determinar período
    if period == "day":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = now
    elif period == "week":
        start = now - timedelta(days=now.weekday())
        start = start.replace(hour=0, minute=0, second=0, microsecond=0)
        end = now
    elif period == "year":
        start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        end = now
    else:  # month (default)
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end = now
    
    # Sobrescribir si se proporcionan fechas custom
    if start_date and end_date:
        start = start_date
        end = end_date
        period = "custom"
    
    # Calcular métricas
    metrics = calculate_financial_metrics(FINANCIAL_RECORDS_DB, start, end)
    
    return FinancialDashboard(
        period=period,
        revenue=metrics["revenue"],
        costs=metrics["costs"],
        expenses=metrics["expenses"],
        waste_cost=metrics["waste_cost"],
        gross_profit=metrics["gross_profit"],
        net_profit=metrics["net_profit"],
        margin_percent=metrics["margin_percent"],
        profit_margin_percent=metrics["profit_margin_percent"],
        trends=metrics["trends"],
        top_categories=metrics["top_categories"],
        alerts=metrics["alerts"],
    )


@router.post("/records", status_code=status.HTTP_201_CREATED, summary="Crear registro financiero")
async def create_financial_record(record: FinancialRecordCreate) -> dict:
    """Crea un nuevo registro financiero."""
    import uuid
    
    record_id = f"fr-{uuid.uuid4().hex[:8]}"
    
    record_data = {
        "id": record_id,
        "type": record.record_type,
        "category": record.category,
        "amount": record.amount,
        "date": (record.date or datetime.now(timezone.utc)).isoformat(),
        "description": record.description,
        "location_id": record.location_id,
    }
    
    FINANCIAL_RECORDS_DB.append(record_data)
    
    return {
        "success": True,
        "record_id": record_id,
        "message": f"Registro {record.record_type} creado exitosamente",
    }


@router.get("/records", summary="Listar registros financieros")
async def list_financial_records(
    record_type: str | None = None,
    category: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    limit: int = 100,
) -> list[dict]:
    """Lista registros financieros con filtros."""
    records = FINANCIAL_RECORDS_DB.copy()
    
    if record_type:
        records = [r for r in records if r["type"] == record_type]
    if category:
        records = [r for r in records if r["category"] == category]
    if start_date:
        records = [r for r in records if parse_date(r["date"]) >= start_date]
    if end_date:
        records = [r for r in records if parse_date(r["date"]) <= end_date]
    
    # Ordenar por fecha descendente
    records.sort(key=lambda x: x["date"], reverse=True)
    
    return records[:limit]


@router.get("/waste-analysis", summary="Análisis de mermas")
async def get_waste_analysis(
    period: str = "month",
) -> dict:
    """Análisis detallado de mermas."""
    now = datetime.now(timezone.utc)
    
    if period == "week":
        start = now - timedelta(days=7)
    elif period == "year":
        start = now.replace(month=1, day=1)
    else:
        start = now.replace(day=1)
    
    # Filtrar registros de waste
    waste_records = [
        r for r in FINANCIAL_RECORDS_DB
        if r["type"] == "waste" and parse_date(r["date"]) >= start
    ]
    
    total_waste = sum(r["amount"] for r in waste_records)
    
    # Agrupar por categoría
    by_category: dict[str, float] = {}
    by_reason: dict[str, float] = {}
    
    for r in waste_records:
        cat = r["category"]
        by_category[cat] = by_category.get(cat, 0) + r["amount"]
        
        # Extraer razón de la descripción (simplificado)
        desc = r.get("description", "").lower()
        if "caduc" in desc:
            reason = "caducidad"
        elif "merma" in desc:
            reason = "preparación"
        elif "dañ" in desc:
            reason = "daño"
        else:
            reason = "otros"
        
        by_reason[reason] = by_reason.get(reason, 0) + r["amount"]
    
    # Calcular impacto
    total_revenue = sum(
        r["amount"] for r in FINANCIAL_RECORDS_DB
        if r["type"] == "revenue" and parse_date(r["date"]) >= start
    )
    
    waste_percent = (total_waste / total_revenue * 100) if total_revenue > 0 else 0
    
    return {
        "period": period,
        "total_waste": round(total_waste, 2),
        "waste_percent_of_revenue": round(waste_percent, 2),
        "by_category": by_category,
        "by_reason": by_reason,
        "records": waste_records,
        "recommendations": [
            "Revisar procedimientos de almacenamiento" if waste_percent > 3 else "Mermas dentro de rango aceptable",
            "Capacitar personal en manejo de ingredientes",
            "Implementar sistema FIFO (primero en entrar, primero en salir)",
        ] if waste_percent > 3 else ["Continuar monitoreo"],
    }


@router.get("/profit-trend", summary="Tendencia de ganancias")
async def get_profit_trend(
    months: int = 6,
) -> list[dict]:
    """Obtiene tendencia de ganancias por mes."""
    now = datetime.now(timezone.utc)
    trend = []
    
    for i in range(months):
        # Calcular primer y último día del mes
        if i == 0:
            end = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
            start = end.replace(day=1)
        else:
            end = start - timedelta(days=1)
            start = end.replace(day=1)
        
        metrics = calculate_financial_metrics(FINANCIAL_RECORDS_DB, start, end)
        
        trend.append({
            "month": start.strftime("%Y-%m"),
            "revenue": metrics["revenue"],
            "gross_profit": metrics["gross_profit"],
            "net_profit": metrics["net_profit"],
            "margin_percent": metrics["margin_percent"],
        })
    
    # Ordenar cronológicamente
    trend.reverse()
    
    return trend


@router.get("/export", summary="Exportar reporte")
async def export_financial_report(
    format: str = "csv",  # csv, json
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> dict:
    """Exporta reporte financiero en formato CSV o JSON."""
    # En producción: generar archivo real
    # Aquí solo simulamos la respuesta
    
    now = datetime.now(timezone.utc)
    start = start_date or (now - timedelta(days=30))
    end = end_date or now
    
    metrics = calculate_financial_metrics(FINANCIAL_RECORDS_DB, start, end)
    
    return {
        "format": format,
        "period": f"{start.isoformat()} to {end.isoformat()}",
        "generated_at": now.isoformat(),
        "data": metrics,
        "download_url": f"/api/v1/financial/export/download?format={format}&start={start.isoformat()}&end={end.isoformat()}",
        "message": f"Reporte {format.upper()} generado exitosamente",
    }
