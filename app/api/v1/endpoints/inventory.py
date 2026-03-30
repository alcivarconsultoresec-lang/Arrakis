"""Endpoints para inventario y recomendaciones."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/inventory", tags=["inventory"])


# ============================================================================
# SCHEMAS
# ============================================================================

class InventoryItem(BaseModel):
    """Item de inventario."""
    id: str
    name: str
    category: str | None = None
    current_stock: float
    unit_of_measure: str
    min_threshold: float
    max_threshold: float
    unit_cost: float
    total_value: float
    location_id: str | None = None


class InventoryMovementCreate(BaseModel):
    """Registrar movimiento de inventario."""
    item_id: str
    movement_type: str  # purchase, consumption, waste, adjustment, sale
    quantity: float
    unit_cost: float | None = None
    reference: str | None = None
    notes: str | None = None


class PurchaseOrderItem(BaseModel):
    """Item de orden de compra."""
    ingredient_id: str
    ingredient_name: str
    quantity: float
    unit_of_measure: str
    estimated_cost: float


class PurchaseOrderCreate(BaseModel):
    """Crear orden de compra."""
    location_id: str
    supplier_name: str
    items: list[PurchaseOrderItem] = Field(default_factory=list)
    notes: str | None = None
    expected_delivery: datetime | None = None


class Recommendation(BaseModel):
    """Recomendación del sistema."""
    id: str
    type: str  # low_stock, waste_alert, purchase_suggestion, optimization
    priority: str  # high, medium, low
    title: str
    message: str
    action: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ============================================================================
# MOCK DATA
# ============================================================================

INVENTORY_DB: dict[str, dict] = {
    "inv-1": {
        "id": "inv-1",
        "name": "Tomate",
        "category": "verduras",
        "current_stock": 15.5,
        "unit_of_measure": "kg",
        "min_threshold": 10.0,
        "max_threshold": 50.0,
        "unit_cost": 35.0,
        "location_id": "loc-1",
    },
    "inv-2": {
        "id": "inv-2",
        "name": "Cerdo",
        "category": "proteinas",
        "current_stock": 8.0,
        "unit_of_measure": "kg",
        "min_threshold": 10.0,
        "max_threshold": 30.0,
        "unit_cost": 120.0,
        "location_id": "loc-1",
    },
    "inv-3": {
        "id": "inv-3",
        "name": "Aguacate",
        "category": "verduras",
        "current_stock": 25.0,
        "unit_of_measure": "kg",
        "min_threshold": 15.0,
        "max_threshold": 40.0,
        "unit_cost": 80.0,
        "location_id": "loc-1",
    },
    "inv-4": {
        "id": "inv-4",
        "name": "Tortillas",
        "category": "abarrotes",
        "current_stock": 100.0,
        "unit_of_measure": "units",
        "min_threshold": 200.0,
        "max_threshold": 500.0,
        "unit_cost": 2.0,
        "location_id": "loc-1",
    },
}

MOVEMENTS_DB: list[dict] = []
PURCHASE_ORDERS_DB: dict[str, dict] = {}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def calculate_total_value(stock: float, unit_cost: float) -> float:
    """Calcula valor total del inventario."""
    return round(stock * unit_cost, 2)


def generate_recommendations() -> list[Recommendation]:
    """Genera recomendaciones basadas en estado actual del inventario."""
    recommendations = []
    
    for item_id, item in INVENTORY_DB.items():
        current = item["current_stock"]
        min_thresh = item["min_threshold"]
        max_thresh = item["max_threshold"]
        
        # Stock bajo
        if current <= min_thresh:
            severity = "high" if current <= 0 else "medium"
            recommendations.append(Recommendation(
                id=f"rec-{item_id}-low",
                type="low_stock",
                priority=severity,
                title=f"Stock bajo: {item['name']}",
                message=f"El stock actual es {current} {item['unit_of_measure']} (umbral mínimo: {min_thresh})",
                action="create_purchase_order",
                metadata={
                    "item_id": item_id,
                    "item_name": item["name"],
                    "current_stock": current,
                    "suggested_quantity": min_thresh * 2 - current,
                },
            ))
        
        # Stock excesivo
        if current >= max_thresh * 0.9:
            recommendations.append(Recommendation(
                id=f"rec-{item_id}-excess",
                type="excess_stock",
                priority="low",
                title=f"Stock alto: {item['name']}",
                message=f"El stock actual es {current} {item['unit_of_measure']} (máximo recomendado: {max_thresh})",
                action="review_consumption",
                metadata={
                    "item_id": item_id,
                    "item_name": item["name"],
                    "current_stock": current,
                },
            ))
    
    # Ordenar por prioridad
    priority_order = {"high": 0, "medium": 1, "low": 2}
    recommendations.sort(key=lambda r: priority_order.get(r.priority, 3))
    
    return recommendations


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("", response_model=list[InventoryItem], summary="Listar inventario")
async def list_inventory(
    location_id: str | None = None,
    category: str | None = None,
    low_stock_only: bool = False,
) -> list[InventoryItem]:
    """Lista todos los items de inventario con filtros opcionales."""
    items = []
    
    for item_data in INVENTORY_DB.values():
        # Aplicar filtros
        if location_id and item_data.get("location_id") != location_id:
            continue
        if category and item_data.get("category") != category:
            continue
        if low_stock_only and item_data["current_stock"] > item_data["min_threshold"]:
            continue
        
        total_value = calculate_total_value(item_data["current_stock"], item_data["unit_cost"])
        
        items.append(InventoryItem(
            id=item_data["id"],
            name=item_data["name"],
            category=item_data.get("category"),
            current_stock=item_data["current_stock"],
            unit_of_measure=item_data["unit_of_measure"],
            min_threshold=item_data["min_threshold"],
            max_threshold=item_data["max_threshold"],
            unit_cost=item_data["unit_cost"],
            total_value=total_value,
            location_id=item_data.get("location_id"),
        ))
    
    return items


@router.get("/recommendations", response_model=list[Recommendation], summary="Obtener recomendaciones")
async def get_inventory_recommendations(
    location_id: str | None = None,
    priority: str | None = None,
) -> list[Recommendation]:
    """
    **Obtiene recomendaciones inteligentes de inventario.**
    
    Basado en reglas determinísticas:
    - Alertas de stock bajo/crítico
    - Exceso de inventario
    - Sugerencias de reorden
    - Optimización de costos
    
    Las recomendaciones se generan en tiempo real según el estado actual.
    """
    recommendations = generate_recommendations()
    
    # Aplicar filtros
    if location_id:
        # Filtrar por ubicación (en producción: query más sofisticada)
        pass
    
    if priority:
        recommendations = [r for r in recommendations if r.priority == priority]
    
    return recommendations


@router.post("/movements", status_code=status.HTTP_201_CREATED, summary="Registrar movimiento")
async def create_movement(movement: InventoryMovementCreate) -> dict:
    """Registra un movimiento de inventario (entrada/salida)."""
    if movement.item_id not in INVENTORY_DB:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item {movement.item_id} no encontrado",
        )
    
    item = INVENTORY_DB[movement.item_id]
    
    # Actualizar stock
    if movement.movement_type in ["purchase", "adjustment"]:
        item["current_stock"] += movement.quantity
    elif movement.movement_type in ["consumption", "waste", "sale"]:
        item["current_stock"] -= movement.quantity
        
        # Validar stock negativo
        if item["current_stock"] < 0:
            logger.warning(f"Stock negativo para {item['name']}: {item['current_stock']}")
    
    # Registrar movimiento
    movement_record = {
        "id": f"mov-{len(MOVEMENTS_DB) + 1}",
        "item_id": movement.item_id,
        "movement_type": movement.movement_type,
        "quantity": movement.quantity,
        "unit_cost": movement.unit_cost or item["unit_cost"],
        "reference": movement.reference,
        "notes": movement.notes,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    MOVEMENTS_DB.append(movement_record)
    
    return {
        "success": True,
        "message": f"Movimiento registrado: {movement.movement_type} {movement.quantity} {item['unit_of_measure']}",
        "new_stock": item["current_stock"],
        "movement_id": movement_record["id"],
    }


@router.get("/movements", summary="Historial de movimientos")
async def list_movements(
    item_id: str | None = None,
    movement_type: str | None = None,
    limit: int = 50,
) -> list[dict]:
    """Lista historial de movimientos con filtros."""
    movements = MOVEMENTS_DB.copy()
    
    if item_id:
        movements = [m for m in movements if m["item_id"] == item_id]
    if movement_type:
        movements = [m for m in movements if m["movement_type"] == movement_type]
    
    # Ordenar por fecha descendente
    movements.sort(key=lambda x: x["timestamp"], reverse=True)
    
    return movements[:limit]


@router.post("/purchase-orders", status_code=status.HTTP_201_CREATED, summary="Crear orden de compra")
async def create_purchase_order(order: PurchaseOrderCreate) -> dict:
    """Crea una orden de compra a proveedor."""
    import uuid
    
    order_id = f"po-{uuid.uuid4().hex[:8]}"
    
    # Calcular total
    total_amount = sum(item.estimated_cost * item.quantity for item in order.items)
    
    order_data = {
        "id": order_id,
        "location_id": order.location_id,
        "supplier_name": order.supplier_name,
        "status": "pending",
        "total_amount": round(total_amount, 2),
        "items": [item.model_dump() for item in order.items],
        "notes": order.notes,
        "expected_delivery": order.expected_delivery.isoformat() if order.expected_delivery else None,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    
    PURCHASE_ORDERS_DB[order_id] = order_data
    
    return {
        "success": True,
        "order_id": order_id,
        "total_amount": round(total_amount, 2),
        "message": f"Orden de compra creada para {order.supplier_name}",
    }


@router.get("/purchase-orders", summary="Listar órdenes de compra")
async def list_purchase_orders(
    status_filter: str | None = None,
    location_id: str | None = None,
) -> list[dict]:
    """Lista órdenes de compra con filtros."""
    orders = list(PURCHASE_ORDERS_DB.values())
    
    if status_filter:
        orders = [o for o in orders if o["status"] == status_filter]
    if location_id:
        orders = [o for o in orders if o["location_id"] == location_id]
    
    return orders


@router.get("/summary", summary="Resumen de inventario")
async def get_inventory_summary() -> dict:
    """Obtiene resumen general del inventario."""
    total_items = len(INVENTORY_DB)
    total_value = sum(
        calculate_total_value(item["current_stock"], item["unit_cost"])
        for item in INVENTORY_DB.values()
    )
    
    low_stock_count = sum(
        1 for item in INVENTORY_DB.values()
        if item["current_stock"] <= item["min_threshold"]
    )
    
    out_of_stock = [
        item["name"] for item in INVENTORY_DB.values()
        if item["current_stock"] <= 0
    ]
    
    return {
        "total_items": total_items,
        "total_value": round(total_value, 2),
        "low_stock_count": low_stock_count,
        "out_of_stock_items": out_of_stock,
        "categories": list(set(item.get("category", "uncategorized") for item in INVENTORY_DB.values())),
    }
