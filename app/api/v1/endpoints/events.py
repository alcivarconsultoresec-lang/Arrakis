"""Endpoints para cotización de eventos."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, EmailStr

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/events", tags=["events"])


# ============================================================================
# SCHEMAS
# ============================================================================

class MenuItemRequest(BaseModel):
    """Item de menú para evento."""
    recipe_id: str
    recipe_name: str
    servings_per_batch: int
    batches_needed: int
    cost_per_batch: float


class EventQuoteRequest(BaseModel):
    """Solicitud de cotización de evento."""
    customer_name: str
    customer_email: EmailStr | None = None
    customer_phone: str | None = None
    event_date: datetime
    event_type: str | None = None  # boda, corporativo, fiesta, etc.
    guest_count: int = Field(..., ge=1, le=10000)
    menu_items: list[MenuItemRequest] = Field(default_factory=list)
    service_type: str = "standard"  # standard, premium, deluxe
    notes: str | None = None


class EventQuoteResponse(BaseModel):
    """Respuesta de cotización de evento."""
    quote_id: str
    status: str
    customer_name: str
    event_date: datetime
    guest_count: int
    menu_summary: list[dict]
    subtotal: float
    service_fee: float
    tax: float
    total_price: float
    total_cost: float
    margin_percent: float
    price_per_guest: float
    recommendations: list[str]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class QuoteApprovalRequest(BaseModel):
    """Aprobación/rechazo de cotización."""
    approved: bool
    notes: str | None = None


# ============================================================================
# MOCK DATA
# ============================================================================

EVENT_QUOTES_DB: dict[str, dict] = {}

# Costos por tipo de servicio (por persona)
SERVICE_COSTS = {
    "standard": {"base_cost": 150, "service_fee_percent": 10},
    "premium": {"base_cost": 250, "service_fee_percent": 15},
    "deluxe": {"base_cost": 400, "service_fee_percent": 20},
}

TAX_RATE = 0.16  # 16% IVA


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def calculate_event_quote(request: EventQuoteRequest) -> dict[str, Any]:
    """Calcula cotización detallada del evento."""
    
    # Calcular costos de menú
    menu_costs = []
    total_food_cost = 0
    
    for item in request.menu_items:
        batch_cost = item.cost_per_batch * item.batches_needed
        total_food_cost += batch_cost
        menu_costs.append({
            "recipe_name": item.recipe_name,
            "batches": item.batches_needed,
            "cost": round(batch_cost, 2),
        })
    
    # Si no hay menú específico, usar costo base por persona
    if not request.menu_items:
        service_info = SERVICE_COSTS.get(request.service_type, SERVICE_COSTS["standard"])
        total_food_cost = service_info["base_cost"] * request.guest_count * 0.6  # 60% es costo de comida
    
    # Calcular服务费
    service_info = SERVICE_COSTS.get(request.service_type, SERVICE_COSTS["standard"])
    service_fee = total_food_cost * (service_info["service_fee_percent"] / 100)
    
    # Subtotal
    subtotal = total_food_cost + service_fee
    
    # Impuestos
    tax = subtotal * TAX_RATE
    
    # Total
    total_price = subtotal + tax
    
    # Margen estimado (asumiendo que el precio incluye ~35% margen)
    estimated_cost = total_food_cost * 1.15  # 15% overhead adicional
    margin = ((total_price - estimated_cost - tax) / total_price) * 100 if total_price > 0 else 0
    
    # Precio por persona
    price_per_guest = total_price / request.guest_count if request.guest_count > 0 else 0
    
    # Generar recomendaciones
    recommendations = generate_event_recommendations(request, total_price, price_per_guest)
    
    return {
        "menu_costs": menu_costs,
        "total_food_cost": round(total_food_cost, 2),
        "service_fee": round(service_fee, 2),
        "subtotal": round(subtotal, 2),
        "tax": round(tax, 2),
        "total_price": round(total_price, 2),
        "estimated_cost": round(estimated_cost, 2),
        "margin_percent": round(margin, 2),
        "price_per_guest": round(price_per_guest, 2),
        "recommendations": recommendations,
    }


def generate_event_recommendations(
    request: EventQuoteRequest,
    total_price: float,
    price_per_guest: float,
) -> list[str]:
    """Genera recomendaciones para el evento."""
    recommendations = []
    
    # Recomendaciones basadas en tamaño
    if request.guest_count > 200:
        recommendations.append("Evento grande: considerar personal adicional y logística especial")
    
    if request.guest_count < 20:
        recommendations.append("Evento íntimo: sugerir menú degustación o experiencia personalizada")
    
    # Recomendaciones basadas en precio
    if price_per_guest < 200:
        recommendations.append("Precio competitivo - buen valor para el mercado")
    elif price_per_guest > 500:
        recommendations.append("Evento premium - asegurar nivel de servicio acorde")
    
    # Recomendaciones basadas en tipo
    if request.event_type == "boda":
        recommendations.append("Considerar opción de backup para clima adverso")
    elif request.event_type == "corporativo":
        recommendations.append("Incluir opciones vegetarianas y alergenos claramente marcados")
    
    # Temporada (simplificado)
    month = request.event_date.month
    if month in [12, 1, 5]:  # Meses altos
        recommendations.append("Mes de alta demanda - confirmar disponibilidad lo antes posible")
    
    return recommendations


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/calculate-quote", response_model=EventQuoteResponse, summary="Calcular cotización de evento")
async def calculate_event_quote_endpoint(request: EventQuoteRequest) -> EventQuoteResponse:
    """
    **Calcula cotización detallada para evento/catering.**
    
    Considera:
    - Número de invitados
    - Menú seleccionado (recetas con costos)
    - Tipo de servicio (standard, premium, deluxe)
    -服务费 e impuestos
    
    Devuelve:
    - Desglose de costos
    - Precio total y por persona
    - Margen estimado
    - Recomendaciones personalizadas
    """
    import uuid
    
    # Calcular cotización
    quote_data = calculate_event_quote(request)
    
    # Generar ID único
    quote_id = f"quote-{uuid.uuid4().hex[:8]}"
    
    # Guardar cotización
    quote_record = {
        "id": quote_id,
        "customer_name": request.customer_name,
        "customer_email": request.customer_email,
        "customer_phone": request.customer_phone,
        "event_date": request.event_date.isoformat(),
        "event_type": request.event_type,
        "guest_count": request.guest_count,
        "service_type": request.service_type,
        "menu_items": [item.model_dump() for item in request.menu_items],
        "status": "draft",
        "pricing": quote_data,
        "notes": request.notes,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    
    EVENT_QUOTES_DB[quote_id] = quote_record
    
    # Construir resumen de menú
    menu_summary = quote_data["menu_costs"] if quote_data["menu_costs"] else [
        {"description": f"Menú {request.service_type}", "cost_per_person": quote_data["total_food_cost"] / request.guest_count if request.guest_count > 0 else 0}
    ]
    
    return EventQuoteResponse(
        quote_id=quote_id,
        status="draft",
        customer_name=request.customer_name,
        event_date=request.event_date,
        guest_count=request.guest_count,
        menu_summary=menu_summary,
        subtotal=quote_data["subtotal"],
        service_fee=quote_data["service_fee"],
        tax=quote_data["tax"],
        total_price=quote_data["total_price"],
        total_cost=quote_data["estimated_cost"],
        margin_percent=quote_data["margin_percent"],
        price_per_guest=quote_data["price_per_guest"],
        recommendations=quote_data["recommendations"],
    )


@router.get("/quotes/{quote_id}", summary="Obtener cotización por ID")
async def get_quote(quote_id: str) -> dict:
    """Obtiene detalles de una cotización específica."""
    if quote_id not in EVENT_QUOTES_DB:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cotización {quote_id} no encontrada",
        )
    
    return EVENT_QUOTES_DB[quote_id]


@router.post("/quotes/{quote_id}/approve", summary="Aprobar/rechazar cotización")
async def approve_quote(quote_id: str, approval: QuoteApprovalRequest) -> dict:
    """Aprueba o rechaza una cotización."""
    if quote_id not in EVENT_QUOTES_DB:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cotización {quote_id} no encontrada",
        )
    
    quote = EVENT_QUOTES_DB[quote_id]
    quote["status"] = "accepted" if approval.approved else "rejected"
    quote["approval_notes"] = approval.notes
    quote["approved_at"] = datetime.now(timezone.utc).isoformat()
    
    return {
        "success": True,
        "quote_id": quote_id,
        "status": quote["status"],
        "message": "Cotización aceptada" if approval.approved else "Cotización rechazada",
    }


@router.get("/quotes", summary="Listar cotizaciones")
async def list_quotes(
    status_filter: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> list[dict]:
    """Lista cotizaciones con filtros opcionales."""
    quotes = list(EVENT_QUOTES_DB.values())
    
    if status_filter:
        quotes = [q for q in quotes if q["status"] == status_filter]
    
    if date_from:
        quotes = [q for q in quotes if q["event_date"] >= date_from.isoformat()]
    
    if date_to:
        quotes = [q for q in quotes if q["event_date"] <= date_to.isoformat()]
    
    # Ordenar por fecha de creación descendente
    quotes.sort(key=lambda x: x["created_at"], reverse=True)
    
    return quotes


@router.delete("/quotes/{quote_id}", summary="Eliminar cotización")
async def delete_quote(quote_id: str) -> dict:
    """Elimina una cotización."""
    if quote_id not in EVENT_QUOTES_DB:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cotización {quote_id} no encontrada",
        )
    
    del EVENT_QUOTES_DB[quote_id]
    return {"success": True, "message": f"Cotización {quote_id} eliminada"}


@router.get("/templates", summary="Plantillas de eventos")
async def get_event_templates() -> list[dict]:
    """Obtiene plantillas predefinidas para tipos de eventos."""
    return [
        {
            "type": "boda",
            "name": "Boda Tradicional",
            "avg_guests": 150,
            "service_type": "premium",
            "description": "Servicio completo para boda con cena de 3 tiempos",
            "price_range": "$350-500 por persona",
        },
        {
            "type": "corporativo",
            "name": "Evento Corporativo",
            "avg_guests": 50,
            "service_type": "standard",
            "description": "Coffee break o lunch ejecutivo",
            "price_range": "$150-250 por persona",
        },
        {
            "type": "fiesta",
            "name": "Fiesta Privada",
            "avg_guests": 30,
            "service_type": "standard",
            "description": "Fiesta de cumpleaños o celebración familiar",
            "price_range": "$200-350 por persona",
        },
        {
            "type": "catering",
            "name": "Catering Drop-off",
            "avg_guests": 20,
            "service_type": "standard",
            "description": "Entrega de alimentos sin servicio en sitio",
            "price_range": "$100-180 por persona",
        },
    ]
