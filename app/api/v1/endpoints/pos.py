"""Endpoints para integración POS."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pos", tags=["pos"])


# ============================================================================
# SCHEMAS
# ============================================================================

class POSIntegrationConfig(BaseModel):
    """Configuración de integración POS."""
    provider: str  # toast, square, clover, custom
    api_key: str
    location_ids: list[str] = Field(default_factory=list)
    sync_enabled: bool = True
    webhook_url: str | None = None


class POSSalesData(BaseModel):
    """Datos de ventas del POS."""
    transaction_id: str
    amount: float
    items: list[dict]
    timestamp: datetime
    location_id: str
    payment_method: str


class POSWebhookPayload(BaseModel):
    """Payload de webhook del POS."""
    event_type: str  # sale.created, refund.created, etc.
    data: dict[str, Any]
    timestamp: datetime


# ============================================================================
# MOCK DATA
# ============================================================================

POS_INTEGRATIONS_DB: dict[str, dict] = {}
POS_SALES_CACHE: list[dict] = []

# Proveedores soportados
SUPPORTED_PROVIDERS = {
    "toast": {
        "name": "Toast POS",
        "auth_type": "api_key",
        "webhook_support": True,
        "features": ["sales", "inventory", "menu"],
    },
    "square": {
        "name": "Square POS",
        "auth_type": "oauth2",
        "webhook_support": True,
        "features": ["sales", "inventory", "customers"],
    },
    "clover": {
        "name": "Clover POS",
        "auth_type": "api_key",
        "webhook_support": True,
        "features": ["sales", "inventory"],
    },
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def simulate_pos_sync(provider: str, api_key: str) -> list[dict]:
    """Simula sincronización con POS (mock data)."""
    import random
    
    now = datetime.now(timezone.utc)
    sales = []
    
    for i in range(random.randint(5, 20)):
        sale = {
            "transaction_id": f"txn-{provider}-{i}",
            "amount": round(random.uniform(50, 500), 2),
            "items": [
                {"name": "Item 1", "quantity": 2, "price": 50},
                {"name": "Item 2", "quantity": 1, "price": 75},
            ],
            "timestamp": (now.replace(hour=random.randint(8, 22), minute=random.randint(0, 59))).isoformat(),
            "location_id": f"loc-{random.randint(1, 3)}",
            "payment_method": random.choice(["credit_card", "debit_card", "cash"]),
        }
        sales.append(sale)
    
    return sales


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/integrations", status_code=status.HTTP_201_CREATED, summary="Configurar integración POS")
async def configure_pos_integration(config: POSIntegrationConfig) -> dict:
    """
    **Configura integración con sistema POS.**
    
    Proveedores soportados:
    - Toast POS
    - Square POS
    - Clover POS
    - Custom (webhook-based)
    
    La configuración incluye:
    - Credenciales de API
    - Ubicaciones a sincronizar
    - URL de webhook para actualizaciones en tiempo real
    """
    import uuid
    
    provider = config.provider.lower()
    
    if provider not in SUPPORTED_PROVIDERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Proveedor no soportado. Opciones: {list(SUPPORTED_PROVIDERS.keys())}",
        )
    
    integration_id = f"pos-{uuid.uuid4().hex[:8]}"
    
    # En producción: validar credenciales con el proveedor
    # Aquí solo simulamos
    
    integration_data = {
        "id": integration_id,
        "provider": provider,
        "provider_name": SUPPORTED_PROVIDERS[provider]["name"],
        "api_key_masked": f"{config.api_key[:4]}...{config.api_key[-4:]}" if len(config.api_key) > 8 else "***",
        "location_ids": config.location_ids,
        "sync_enabled": config.sync_enabled,
        "webhook_url": config.webhook_url,
        "status": "active",
        "last_sync": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    
    POS_INTEGRATIONS_DB[integration_id] = integration_data
    
    return {
        "success": True,
        "integration_id": integration_id,
        "message": f"Integración con {SUPPORTED_PROVIDERS[provider]['name']} configurada exitosamente",
        "next_steps": [
            "Verificar conexión con prueba de sincronización",
            "Configurar webhook para actualizaciones en tiempo real",
            "Seleccionar ubicaciones a sincronizar",
        ],
    }


@router.get("/integrations", summary="Listar integraciones POS")
async def list_pos_integrations() -> list[dict]:
    """Lista todas las integraciones POS configuradas."""
    return list(POS_INTEGRATIONS_DB.values())


@router.get("/integrations/{integration_id}", summary="Obtener integración POS")
async def get_pos_integration(integration_id: str) -> dict:
    """Obtiene detalles de una integración específica."""
    if integration_id not in POS_INTEGRATIONS_DB:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Integración {integration_id} no encontrada",
        )
    
    return POS_INTEGRATIONS_DB[integration_id]


@router.post("/integrations/{integration_id}/sync", summary="Sincronizar con POS")
async def sync_pos_integration(integration_id: str) -> dict:
    """Ejecuta sincronización manual con el POS."""
    if integration_id not in POS_INTEGRATIONS_DB:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Integración {integration_id} no encontrada",
        )
    
    integration = POS_INTEGRATIONS_DB[integration_id]
    provider = integration["provider"]
    
    # Simular sincronización
    logger.info(f"Starting POS sync for {integration_id} ({provider})")
    
    # En producción: llamar API del proveedor
    sales_data = simulate_pos_sync(provider, "mock-api-key")
    
    # Actualizar última sincronización
    integration["last_sync"] = datetime.now(timezone.utc).isoformat()
    integration["total_transactions_synced"] = integration.get("total_transactions_synced", 0) + len(sales_data)
    
    # Cache de ventas para reporting
    POS_SALES_CACHE.extend(sales_data)
    
    return {
        "success": True,
        "integration_id": integration_id,
        "transactions_synced": len(sales_data),
        "total_revenue": sum(s["amount"] for s in sales_data),
        "last_sync": integration["last_sync"],
        "message": f"Sincronización completada: {len(sales_data)} transacciones importadas",
    }


@router.get("/providers", summary="Listar proveedores POS soportados")
async def list_pos_providers() -> list[dict]:
    """Lista todos los proveedores POS disponibles."""
    return [
        {
            "id": key,
            **info,
        }
        for key, info in SUPPORTED_PROVIDERS.items()
    ]


@router.post("/webhook/{integration_id}", summary="Webhook para actualizaciones POS")
async def pos_webhook(integration_id: str, payload: POSWebhookPayload) -> dict:
    """
    **Endpoint para recibir webhooks del POS.**
    
    Eventos soportados:
    - sale.created: Nueva venta
    - sale.refunded: Reembolso
    - inventory.updated: Cambio en inventario
    - menu.updated: Actualización de menú
    
    Este endpoint debe ser configurado en el dashboard del proveedor POS.
    """
    if integration_id not in POS_INTEGRATIONS_DB:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Integración {integration_id} no encontrada",
        )
    
    logger.info(f"Received webhook from POS: {payload.event_type}")
    
    # Procesar según tipo de evento
    if payload.event_type == "sale.created":
        # Registrar venta en nuestro sistema
        POS_SALES_CACHE.append({
            **payload.data,
            "source": "webhook",
            "received_at": datetime.now(timezone.utc).isoformat(),
        })
        
        return {"success": True, "message": "Venta registrada"}
    
    elif payload.event_type == "sale.refunded":
        # Buscar y marcar venta como reembolsada
        return {"success": True, "message": "Reembolso procesado"}
    
    elif payload.event_type == "inventory.updated":
        # Actualizar inventario local
        return {"success": True, "message": "Inventario actualizado"}
    
    else:
        logger.warning(f"Unhandled webhook event: {payload.event_type}")
        return {"success": True, "message": "Evento recibido pero no procesado"}


@router.get("/sales/recent", summary="Ventas recientes del POS")
async def get_recent_pos_sales(
    limit: int = 50,
    location_id: str | None = None,
) -> list[dict]:
    """Obtiene ventas recientes sincronizadas del POS."""
    sales = POS_SALES_CACHE.copy()
    
    if location_id:
        sales = [s for s in sales if s.get("location_id") == location_id]
    
    # Ordenar por fecha descendente
    sales.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    
    return sales[:limit]


@router.get("/sales/summary", summary="Resumen de ventas del POS")
async def get_pos_sales_summary(
    days: int = 7,
) -> dict:
    """Resumen estadístico de ventas del POS."""
    now = datetime.now(timezone.utc)
    cutoff = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=days)
    
    # Filtrar ventas del período
    recent_sales = [
        s for s in POS_SALES_CACHE
        if datetime.fromisoformat(s.get("timestamp", "").replace("Z", "+00:00")) >= cutoff
    ]
    
    if not recent_sales:
        return {
            "period_days": days,
            "total_transactions": 0,
            "total_revenue": 0,
            "average_ticket": 0,
            "by_payment_method": {},
            "by_location": {},
        }
    
    # Calcular métricas
    total_revenue = sum(s["amount"] for s in recent_sales)
    avg_ticket = total_revenue / len(recent_sales)
    
    # Agrupar por método de pago
    by_payment: dict[str, float] = {}
    for s in recent_sales:
        method = s.get("payment_method", "unknown")
        by_payment[method] = by_payment.get(method, 0) + s["amount"]
    
    # Agrupar por ubicación
    by_location: dict[str, float] = {}
    for s in recent_sales:
        loc = s.get("location_id", "unknown")
        by_location[loc] = by_location.get(loc, 0) + s["amount"]
    
    return {
        "period_days": days,
        "total_transactions": len(recent_sales),
        "total_revenue": round(total_revenue, 2),
        "average_ticket": round(avg_ticket, 2),
        "by_payment_method": by_payment,
        "by_location": by_location,
        "top_day": max(
            set(s.get("timestamp", "")[:10] for s in recent_sales),
            key=lambda d: sum(s["amount"] for s in recent_sales if s.get("timestamp", "").startswith(d)),
            default=None,
        ),
    }


@router.delete("/integrations/{integration_id}", summary="Eliminar integración POS")
async def delete_pos_integration(integration_id: str) -> dict:
    """Elimina una integración POS."""
    if integration_id not in POS_INTEGRATIONS_DB:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Integración {integration_id} no encontrada",
        )
    
    del POS_INTEGRATIONS_DB[integration_id]
    
    return {
        "success": True,
        "message": f"Integración {integration_id} eliminada",
        "note": "Los datos históricos se mantienen en el sistema",
    }
