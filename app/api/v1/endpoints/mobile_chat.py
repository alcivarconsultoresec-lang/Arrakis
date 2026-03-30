"""Endpoints para chat móvil - Core feature."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.domain.models import ChatMessage
from app.services.rules.engine import RuleEngine, rule_engine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mobile", tags=["mobile-chat"])


# ============================================================================
# SCHEMAS
# ============================================================================

class ChatMessageIn(BaseModel):
    """Mensaje de entrada del usuario."""
    message: str = Field(..., min_length=1, max_length=2000, description="Mensaje del usuario")
    location_id: str | None = Field(None, description="ID de ubicación (opcional)")
    context: dict[str, Any] = Field(default_factory=dict, description="Contexto adicional")


class ChatMessageOut(BaseModel):
    """Respuesta del asistente."""
    response: str = Field(..., description="Respuesta del asistente")
    action: str | None = Field(None, description="Acción sugerida")
    data: dict[str, Any] = Field(default_factory=dict, description="Datos estructurados")
    suggestions: list[str] = Field(default_factory=list, description="Sugerencias de follow-up")


class ChatRequest(BaseModel):
    """Request completo de chat."""
    user_id: str
    message: str
    location_id: str | None = None
    chain_id: str | None = None
    context: dict[str, Any] = Field(default_factory=dict)


class ChatResponse(BaseModel):
    """Respuesta completa de chat."""
    success: bool
    assistant_message: str
    action_taken: str | None = None
    structured_data: dict[str, Any] = Field(default_factory=dict)
    quick_actions: list[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ============================================================================
# INTENT CLASSIFICATION (Rule-based)
# ============================================================================

INTENT_PATTERNS = {
    "report_purchase": ["compr", "buy", "purchase", "adquir", "lleg"],
    "report_waste": ["dañ", "merma", "waste", "bot", "tir", "ech"],
    "report_consumption": ["consum", "us", "gast", "ocup"],
    "check_stock": ["stock", "inventario", "cuánt", "queda", "disponible"],
    "check_recommendations": ["recomend", "suger", "deber", "tengo", "hacer"],
    "recipe_cost": ["costo", "precio", "receta", "margen", "ganancia"],
    "event_quote": ["evento", "cotización", "presupuesto", "catering", "fiesta"],
    "financial_report": ["ventas", "ingresos", "gastos", "financiero", "reporte"],
}


def classify_intent(message: str) -> str:
    """Clasifica la intención del mensaje usando patrones simples."""
    message_lower = message.lower()
    
    for intent, patterns in INTENT_PATTERNS.items():
        if any(pattern in message_lower for pattern in patterns):
            return intent
    
    return "general"


def process_intent(
    intent: str,
    message: str,
    context: dict[str, Any],
    rule_engine: RuleEngine,
) -> tuple[str, str | None, dict[str, Any], list[str]]:
    """Procesa la intención y genera respuesta.
    
    Returns:
        Tuple de (respuesta, acción, datos, sugerencias)
    """
    if intent == "report_purchase":
        # Extraer datos del mensaje
        item = extract_item_from_message(message)
        quantity = extract_quantity_from_message(message)
        
        return (
            f"✅ Compra registrada: {quantity} {item}. ¿Quieres agregar más items?",
            "record_purchase",
            {"item": item, "quantity": quantity, "type": "purchase"},
            ["Registrar otra compra", "Ver inventario actualizado", "Crear orden de compra"],
        )
    
    elif intent == "report_waste":
        item = extract_item_from_message(message)
        quantity = extract_quantity_from_message(message)
        
        return (
            f"⚠️ Merma registrada: {quantity} {item}. Te recomiendo revisar el almacenamiento.",
            "record_waste",
            {"item": item, "quantity": quantity, "type": "waste"},
            ["Reportar causa de merma", "Ver histórico de mermas", "Recibir alertas similares"],
        )
    
    elif intent == "check_stock":
        # Simular consulta de stock (en producción: query a DB)
        inventory_context = context.get("inventory", [])
        
        if inventory_context:
            low_stock = [i for i in inventory_context if i.get("current_stock", 0) <= i.get("min_stock_threshold", 0)]
            if low_stock:
                items_list = ", ".join([f"{i['name']} ({i['current_stock']})" for i in low_stock[:5]])
                return (
                    f"⚠️ Stock bajo detectado: {items_list}. ¿Generar orden de compra?",
                    "show_low_stock",
                    {"low_stock_items": low_stock},
                    ["Generar orden automática", "Ver todo el inventario", "Ajustar umbrales"],
                )
        
        return (
            "✅ Todo el inventario está en niveles adecuados.",
            None,
            {"status": "ok"},
            ["Ver inventario completo", "Configurar alertas", "Ver recomendaciones"],
        )
    
    elif intent == "check_recommendations":
        # Usar Rule Engine para generar recomendaciones
        results = rule_engine.evaluate(context)
        
        if results:
            recommendations = [r.message for r in results if r.triggered]
            actions = [r.action for r in results if r.action]
            
            return (
                f"📋 Recomendaciones:\n" + "\n".join(f"• {r}" for r in recommendations),
                actions[0] if actions else None,
                {"recommendations": [r.__dict__ for r in results]},
                ["Ejecutar acciones sugeridas", "Ver detalles", "Ignorar por ahora"],
            )
        
        return (
            "✅ No hay acciones críticas pendientes. ¡Buen trabajo!",
            None,
            {"status": "no_actions"},
            ["Ver reportes", "Configurar reglas", "Chat general"],
        )
    
    elif intent == "recipe_cost":
        recipe_name = extract_recipe_from_message(message)
        
        return (
            f"📊 Para calcular costos de receta, necesito que selecciones una receta específica.",
            "show_recipes",
            {"recipe_filter": recipe_name},
            ["Ver lista de recetas", "Calcular costo específico", "Optimizar márgenes"],
        )
    
    elif intent == "event_quote":
        return (
            f"📅 Para cotizar un evento, necesito:\n"
            f"• Fecha del evento\n"
            f"• Número de invitados\n"
            f"• Menú o tipo de servicio\n\n"
            f"¿Me puedes dar estos detalles?",
            "start_event_quote",
            {},
            ["Cotizar evento corporativo", "Cotizar boda", "Cotizar fiesta privada"],
        )
    
    elif intent == "financial_report":
        return (
            f"💰 Reporte financiero:\n"
            f"• Selecciona el período (semana, mes, año)\n"
            f"• Elige tipo de reporte (ingresos, gastos, margen)",
            "show_financial_options",
            {},
            ["Ver este mes", "Comparar vs mes anterior", "Exportar PDF"],
        )
    
    else:  # general
        return (
            f"👋 Hola, soy JARBIS. Puedo ayudarte con:\n"
            f"• Registrar compras, mermas o consumo\n"
            f"• Consultar inventario\n"
            f"• Generar recomendaciones\n"
            f"• Calcular costos de recetas\n"
            f"• Cotizar eventos\n\n"
            f"¿Qué necesitas hoy?",
            None,
            {},
            ["Registrar compra", "Ver inventario", "Recomendaciones", "Cotizar evento"],
        )


def extract_item_from_message(message: str) -> str:
    """Extrae nombre de item del mensaje (simplificado)."""
    # En producción: usar NLP más sofisticado
    words = message.lower().split()
    # Ignorar palabras comunes
    skip_words = ["de", "la", "el", "los", "las", "un", "una", "compré", "compramos", "hay"]
    items = [w for w in words if w not in skip_words and len(w) > 2]
    return items[0] if items else "item-desconocido"


def extract_quantity_from_message(message: str) -> float:
    """Extrae cantidad numérica del mensaje."""
    import re
    numbers = re.findall(r'\d+\.?\d*', message)
    return float(numbers[0]) if numbers else 1.0


def extract_recipe_from_message(message: str) -> str:
    """Extrae nombre de receta del mensaje."""
    # Simplificado - en producción usar NLP
    words = message.lower().split()
    skip_words = ["de", "la", "el", "los", "las", "costo", "precio", "receta"]
    items = [w for w in words if w not in skip_words and len(w) > 2]
    return " ".join(items[:3]) if items else ""


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/chat", response_model=ChatResponse, summary="Chat principal con asistente")
async def mobile_chat(request: ChatRequest) -> ChatResponse:
    """
    **Endpoint principal de chat móvil.**
    
    Procesa mensajes naturales del usuario, clasifica la intención,
    ejecuta reglas determinísticas y devuelve respuesta estructurada.
    
    ## Casos de uso:
    - Registrar eventos (compras, mermas, consumo)
    - Consultar inventario
    - Obtener recomendaciones
    - Calcular costos
    - Cotizar eventos
    - Reportes financieros
    
    ## Respuesta:
    Incluye mensaje natural + datos estructurados + acciones rápidas.
    """
    try:
        # 1. Clasificar intención
        intent = classify_intent(request.message)
        logger.info(f"Intent classified: {intent} for user {request.user_id}")
        
        # 2. Preparar contexto para Rule Engine
        context = {
            "inventory": request.context.get("inventory", []),
            "consumption": request.context.get("consumption", []),
            "recipes": request.context.get("recipes", []),
            "user_location": request.location_id,
            "chain_id": request.chain_id,
        }
        
        # 3. Procesar intención y obtener respuesta
        response_text, action, data, suggestions = process_intent(
            intent=intent,
            message=request.message,
            context=context,
            rule_engine=rule_engine,
        )
        
        # 4. Guardar mensaje en historial (opcional, async)
        # await save_chat_message(request.user_id, "user", request.message)
        # await save_chat_message(request.user_id, "assistant", response_text)
        
        return ChatResponse(
            success=True,
            assistant_message=response_text,
            action_taken=action,
            structured_data=data,
            quick_actions=suggestions,
        )
    
    except Exception as e:
        logger.error(f"Error processing chat: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error procesando mensaje: {str(e)}",
        )


@router.get("/chat/history", response_model=list[dict], summary="Historial de chat")
async def get_chat_history(
    user_id: str,
    limit: int = 50,
) -> list[dict]:
    """Obtiene historial de conversaciones del usuario."""
    # TODO: Implementar con DB
    return []


@router.delete("/chat/history", summary="Limpiar historial")
async def clear_chat_history(user_id: str) -> dict:
    """Limpia el historial de chat del usuario."""
    # TODO: Implementar con DB
    return {"success": True, "message": "Historial limpiado"}
