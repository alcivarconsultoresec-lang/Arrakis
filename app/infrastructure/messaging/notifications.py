"""Servicio de notificaciones push."""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class NotificationService:
    """Servicio de notificaciones push (Firebase/FCM).
    
    Para MVP: implementa logging y mock.
    En producción: integrar con Firebase Cloud Messaging.
    """
    
    def __init__(self, firebase_credentials: str | None = None) -> None:
        self.firebase_credentials = firebase_credentials
        self.enabled = firebase_credentials is not None
        
        if self.enabled:
            try:
                # En producción: inicializar Firebase Admin SDK
                # import firebase_admin
                # firebase_admin.initialize_app(...)
                logger.info("Firebase notifications enabled")
            except Exception as e:
                logger.warning(f"Failed to initialize Firebase: {e}")
                self.enabled = False
    
    async def send_push(
        self,
        user_id: str,
        title: str,
        body: str,
        data: dict[str, Any] | None = None,
    ) -> bool:
        """Envía notificación push a un usuario.
        
        Args:
            user_id: ID del usuario
            title: Título de la notificación
            body: Cuerpo del mensaje
            data: Datos adicionales (opcionales)
        
        Returns:
            True si se envió exitosamente
        """
        if not self.enabled:
            # Mock: solo loguear
            logger.info(
                f"[PUSH MOCK] To {user_id}: {title} - {body}",
                extra={"data": data},
            )
            return True
        
        try:
            # En producción: enviar vía FCM
            # message = messaging.Message(...)
            # messaging.send(message)
            logger.info(f"Push sent to {user_id}: {title}")
            return True
        except Exception as e:
            logger.error(f"Failed to send push to {user_id}: {e}")
            return False
    
    async def send_stock_alert(
        self,
        user_id: str,
        item_name: str,
        current_stock: float,
        threshold: float,
    ) -> bool:
        """Envía alerta de stock bajo."""
        return await self.send_push(
            user_id=user_id,
            title="⚠️ Stock Bajo",
            body=f"{item_name}: {current_stock:.2f} unidades (umbral: {threshold:.2f})",
            data={
                "type": "stock_alert",
                "item": item_name,
                "action": "view_inventory",
            },
        )
    
    async def send_order_ready(
        self,
        user_id: str,
        order_id: str,
        items_count: int,
    ) -> bool:
        """Envía notificación de orden de compra lista."""
        return await self.send_push(
            user_id=user_id,
            title="📦 Orden Lista",
            body=f"Orden #{order_id[:8]} con {items_count} items está lista para revisar",
            data={
                "type": "order_ready",
                "order_id": order_id,
                "action": "view_order",
            },
        )
    
    async def send_event_reminder(
        self,
        user_id: str,
        event_name: str,
        event_date: str,
    ) -> bool:
        """Envía recordatorio de evento."""
        return await self.send_push(
            user_id=user_id,
            title="📅 Recordatorio de Evento",
            body=f"{event_name} - {event_date}",
            data={
                "type": "event_reminder",
                "action": "view_events",
            },
        )


# Instancia global (se configura en el startup de la app)
notification_service = NotificationService()
