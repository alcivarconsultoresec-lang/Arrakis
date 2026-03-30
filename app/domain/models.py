"""SQLAlchemy models para Ω JARBIS Enterprise."""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from sqlalchemy.sql.schema import ForeignKey


class Base(DeclarativeBase):
    """Clase base para todos los modelos."""
    
    pass


# ============================================================================
# MODELOS MULTI-TENANT (Chain = Cadena de restaurantes)
# ============================================================================

class Chain(Base):
    """Cadena de restaurantes (tenant principal)."""
    __tablename__ = "chains"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    tax_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    locations = relationship("Location", back_populates="chain", cascade="all, delete-orphan")
    users = relationship("User", back_populates="chain", cascade="all, delete-orphan")
    recipes = relationship("Recipe", back_populates="chain", cascade="all, delete-orphan")
    events = relationship("Event", back_populates="chain", cascade="all, delete-orphan")
    financial_records = relationship("FinancialRecord", back_populates="chain", cascade="all, delete-orphan")


class Location(Base):
    """Ubicación física (restaurante individual dentro de una cadena)."""
    __tablename__ = "locations"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    chain_id: Mapped[str] = mapped_column(String(36), ForeignKey("chains.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    country: Mapped[str] = mapped_column(String(100), default="México")
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    chain = relationship("Chain", back_populates="locations")
    inventory = relationship("InventoryItem", back_populates="location", cascade="all, delete-orphan")
    events = relationship("Event", back_populates="location", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("ix_locations_chain", "chain_id"),
    )


# ============================================================================
# USUARIOS Y AUTENTICACIÓN
# ============================================================================

class User(Base):
    """Usuario del sistema."""
    __tablename__ = "users"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    chain_id: Mapped[str] = mapped_column(String(36), ForeignKey("chains.id"), nullable=False)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(String(50), default="user")  # admin, manager, user
    allowed_locations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON list of location IDs
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    chain = relationship("Chain", back_populates="users")


# ============================================================================
# RECETAS E INGREDIENTES
# ============================================================================

class Ingredient(Base):
    """Ingrediente maestro (catálogo global)."""
    __tablename__ = "ingredients"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # proteína, verdura, lácteo, etc.
    unit_of_measure: Mapped[str] = mapped_column(String(50), default="kg")  # kg, L, units, etc.
    avg_cost_per_unit: Mapped[Decimal] = mapped_column(Numeric(10, 4), default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    recipe_ingredients = relationship("RecipeIngredient", back_populates="ingredient")


class Recipe(Base):
    """Receta de plato/preparación."""
    __tablename__ = "recipes"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    chain_id: Mapped[str] = mapped_column(String(36), ForeignKey("chains.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # entrada, plato fuerte, postre, bebida
    selling_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    target_margin: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=30.0)  # porcentaje
    prep_time_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    chain = relationship("Chain", back_populates="recipes")
    ingredients = relationship("RecipeIngredient", back_populates="recipe", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("ix_recipes_chain", "chain_id"),
    )


class RecipeIngredient(Base):
    """Ingredientes de una receta (tabla intermedia con cantidades)."""
    __tablename__ = "recipe_ingredients"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    recipe_id: Mapped[str] = mapped_column(String(36), ForeignKey("recipes.id"), nullable=False)
    ingredient_id: Mapped[str] = mapped_column(String(36), ForeignKey("ingredients.id"), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    unit_of_measure: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Relationships
    recipe = relationship("Recipe", back_populates="ingredients")
    ingredient = relationship("Ingredient", back_populates="recipe_ingredients")
    
    __table_args__ = (
        UniqueConstraint("recipe_id", "ingredient_id", name="uq_recipe_ingredient"),
    )


# ============================================================================
# INVENTARIO
# ============================================================================

class InventoryItem(Base):
    """Item de inventario en una ubicación específica."""
    __tablename__ = "inventory_items"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    location_id: Mapped[str] = mapped_column(String(36), ForeignKey("locations.id"), nullable=False)
    ingredient_id: Mapped[str] = mapped_column(String(36), ForeignKey("ingredients.id"), nullable=False)
    current_stock: Mapped[Decimal] = mapped_column(Numeric(10, 4), default=0)
    min_stock_threshold: Mapped[Decimal] = mapped_column(Numeric(10, 4), default=0)
    max_stock_threshold: Mapped[Decimal] = mapped_column(Numeric(10, 4), default=0)
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(10, 4), default=0)
    last_updated: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    location = relationship("Location", back_populates="inventory")
    ingredient = relationship("Ingredient")
    movements = relationship("InventoryMovement", back_populates="inventory_item", cascade="all, delete-orphan")
    
    __table_args__ = (
        UniqueConstraint("location_id", "ingredient_id", name="uq_location_ingredient"),
        Index("ix_inventory_location", "location_id"),
    )


class InventoryMovement(Base):
    """Movimiento de inventario (entrada/salida)."""
    __tablename__ = "inventory_movements"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    inventory_item_id: Mapped[str] = mapped_column(String(36), ForeignKey("inventory_items.id"), nullable=False)
    movement_type: Mapped[str] = mapped_column(String(50), nullable=False)  # purchase, consumption, waste, adjustment, sale
    quantity: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=True)
    reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # orden, receta, nota
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    created_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)  # user_id
    
    # Relationships
    inventory_item = relationship("InventoryItem", back_populates="movements")
    
    __table_args__ = (
        Index("ix_movement_inventory", "inventory_item_id"),
        Index("ix_movement_type", "movement_type"),
    )


class PurchaseOrder(Base):
    """Orden de compra a proveedores."""
    __tablename__ = "purchase_orders"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    location_id: Mapped[str] = mapped_column(String(36), ForeignKey("locations.id"), nullable=False)
    supplier_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending")  # pending, approved, received, cancelled
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    expected_delivery: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    created_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    
    # Relationships
    location = relationship("Location")
    items = relationship("PurchaseOrderItem", back_populates="order", cascade="all, delete-orphan")


class PurchaseOrderItem(Base):
    """Items de una orden de compra."""
    __tablename__ = "purchase_order_items"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    order_id: Mapped[str] = mapped_column(String(36), ForeignKey("purchase_orders.id"), nullable=False)
    ingredient_id: Mapped[str] = mapped_column(String(36), ForeignKey("ingredients.id"), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    
    # Relationships
    order = relationship("PurchaseOrder", back_populates="items")
    ingredient = relationship("Ingredient")


# ============================================================================
# EVENTOS Y CHAT
# ============================================================================

class Event(Base):
    """Evento del sistema (para chat y tracking)."""
    __tablename__ = "events"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    chain_id: Mapped[str] = mapped_column(String(36), ForeignKey("chains.id"), nullable=False)
    location_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("locations.id"), nullable=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)  # purchase, sale, waste, consumption, adjustment, chat_message
    payload: Mapped[dict] = mapped_column(String, nullable=False)  # JSON
    source: Mapped[str] = mapped_column(String(50), default="chat")  # chat, pos, manual, api
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    created_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    
    # Relationships
    chain = relationship("Chain", back_populates="events")
    location = relationship("Location", back_populates="events")


class ChatMessage(Base):
    """Mensaje de chat con el asistente."""
    __tablename__ = "chat_messages"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # user, assistant, system
    content: Mapped[str] = mapped_column(Text, nullable=False)
    message_metadata: Mapped[Optional[dict]] = mapped_column(String, nullable=True)  # JSON con contexto adicional
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    __table_args__ = (
        Index("ix_chat_user", "user_id"),
        Index("ix_chat_created", "created_at"),
    )


# ============================================================================
# EVENTOS/COTIZACIONES
# ============================================================================

class EventQuote(Base):
    """Cotización para evento/catering."""
    __tablename__ = "event_quotes"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    chain_id: Mapped[str] = mapped_column(String(36), ForeignKey("chains.id"), nullable=False)
    customer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    customer_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    customer_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    event_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    guest_count: Mapped[int] = mapped_column(Integer, nullable=False)
    menu_items: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array de recetas
    total_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    total_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    margin_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    status: Mapped[str] = mapped_column(String(50), default="draft")  # draft, sent, accepted, rejected, cancelled
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    created_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    
    # Relationships
    chain = relationship("Chain")


# ============================================================================
# FINANZAS
# ============================================================================

class FinancialRecord(Base):
    """Registro financiero."""
    __tablename__ = "financial_records"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    chain_id: Mapped[str] = mapped_column(String(36), ForeignKey("chains.id"), nullable=False)
    location_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("locations.id"), nullable=True)
    record_type: Mapped[str] = mapped_column(String(50), nullable=False)  # revenue, cost, expense, waste
    category: Mapped[str] = mapped_column(String(100), nullable=False)  # food, labor, overhead, etc.
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reference_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)  # ID relacionado (orden, receta, etc.)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    chain = relationship("Chain", back_populates="financial_records")
    location = relationship("Location")
    
    __table_args__ = (
        Index("ix_financial_chain", "chain_id"),
        Index("ix_financial_date", "date"),
        Index("ix_financial_type", "record_type"),
    )


# ============================================================================
# POS INTEGRATION
# ============================================================================

class POSIntegration(Base):
    """Configuración de integración POS."""
    __tablename__ = "pos_integrations"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    chain_id: Mapped[str] = mapped_column(String(36), ForeignKey("chains.id"), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)  # toast, square, clover
    api_key_encrypted: Mapped[str] = mapped_column(String(500), nullable=False)
    webhook_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_sync: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    chain = relationship("Chain")
