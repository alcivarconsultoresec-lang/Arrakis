"""Endpoints para recetas y cálculo de costos."""
from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/recipes", tags=["recipes"])


# ============================================================================
# SCHEMAS
# ============================================================================

class RecipeIngredientCreate(BaseModel):
    """Ingrediente de receta."""
    ingredient_id: str
    ingredient_name: str
    quantity: float
    unit_of_measure: str
    cost_per_unit: float = 0


class RecipeCreate(BaseModel):
    """Crear receta."""
    name: str
    description: str | None = None
    category: str | None = None
    selling_price: float = 0
    target_margin: float = 30.0
    prep_time_minutes: int | None = None
    ingredients: list[RecipeIngredientCreate] = Field(default_factory=list)


class RecipeOut(BaseModel):
    """Receta con información completa."""
    id: str
    name: str
    description: str | None = None
    category: str | None = None
    selling_price: float
    total_cost: float
    actual_margin: float
    target_margin: float
    prep_time_minutes: int | None = None
    ingredients: list[dict] = Field(default_factory=list)


class CostBreakdown(BaseModel):
    """Desglose de costos de receta."""
    recipe_id: str
    recipe_name: str
    total_cost: float
    selling_price: float
    margin_percent: float
    target_margin_percent: float
    is_profitable: bool
    suggested_price: float
    ingredients_breakdown: list[dict]
    recommendations: list[str]


# ============================================================================
# MOCK DATA (para MVP - en producción: DB)
# ============================================================================

RECIPES_DB: dict[str, dict] = {
    "recipe-1": {
        "id": "recipe-1",
        "name": "Tacos al Pastor",
        "description": "Tacos tradicionales con carne de cerdo marinada",
        "category": "plato_fuerte",
        "selling_price": 85.0,
        "target_margin": 35.0,
        "prep_time_minutes": 45,
        "ingredients": [
            {"name": "cerdo", "quantity": 0.2, "unit": "kg", "cost_per_unit": 120, "subtotal": 24},
            {"name": "tortillas", "quantity": 5, "unit": "units", "cost_per_unit": 2, "subtotal": 10},
            {"name": "piña", "quantity": 0.1, "unit": "kg", "cost_per_unit": 25, "subtotal": 2.5},
            {"name": "cilantro", "quantity": 0.02, "unit": "kg", "cost_per_unit": 40, "subtotal": 0.8},
            {"name": "cebolla", "quantity": 0.03, "unit": "kg", "cost_per_unit": 30, "subtotal": 0.9},
        ],
    },
    "recipe-2": {
        "id": "recipe-2",
        "name": "Guacamole",
        "description": "Guacamole tradicional mexicano",
        "category": "entrada",
        "selling_price": 65.0,
        "target_margin": 40.0,
        "prep_time_minutes": 15,
        "ingredients": [
            {"name": "aguacate", "quantity": 0.3, "unit": "kg", "cost_per_unit": 80, "subtotal": 24},
            {"name": "tomate", "quantity": 0.1, "unit": "kg", "cost_per_unit": 35, "subtotal": 3.5},
            {"name": "cebolla", "quantity": 0.05, "unit": "kg", "cost_per_unit": 30, "subtotal": 1.5},
            {"name": "limón", "quantity": 0.05, "unit": "kg", "cost_per_unit": 40, "subtotal": 2},
            {"name": "cilantro", "quantity": 0.01, "unit": "kg", "cost_per_unit": 40, "subtotal": 0.4},
        ],
    },
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def calculate_recipe_cost(ingredients: list[dict]) -> tuple[float, list[dict]]:
    """Calcula costo total y desglose de ingredientes."""
    total_cost = 0
    breakdown = []
    
    for ing in ingredients:
        subtotal = ing.get("quantity", 0) * ing.get("cost_per_unit", 0)
        total_cost += subtotal
        breakdown.append({
            "name": ing.get("name", "unknown"),
            "quantity": ing.get("quantity", 0),
            "unit": ing.get("unit", "units"),
            "cost_per_unit": ing.get("cost_per_unit", 0),
            "subtotal": round(subtotal, 2),
            "percentage": 0,  # Se calcula después
        })
    
    # Calcular porcentajes
    if total_cost > 0:
        for item in breakdown:
            item["percentage"] = round((item["subtotal"] / total_cost) * 100, 1)
    
    return round(total_cost, 2), breakdown


def calculate_margin(selling_price: float, total_cost: float) -> float:
    """Calcula margen porcentual."""
    if selling_price <= 0:
        return 0
    return round(((selling_price - total_cost) / selling_price) * 100, 2)


def suggest_price(total_cost: float, target_margin: float) -> float:
    """Sugiere precio basado en costo y margen objetivo."""
    if target_margin >= 100 or target_margin < 0:
        return total_cost * 2
    return round(total_cost / (1 - target_margin / 100), 2)


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("", response_model=list[RecipeOut], summary="Listar recetas")
async def list_recipes(
    chain_id: str | None = None,
    category: str | None = None,
    active_only: bool = True,
) -> list[RecipeOut]:
    """Lista todas las recetas con opción de filtrado."""
    recipes = []
    
    for recipe_data in RECIPES_DB.values():
        # Aplicar filtros
        if category and recipe_data.get("category") != category:
            continue
        
        # Calcular costo total
        total_cost, _ = calculate_recipe_cost(recipe_data.get("ingredients", []))
        margin = calculate_margin(recipe_data["selling_price"], total_cost)
        
        recipes.append(RecipeOut(
            id=recipe_data["id"],
            name=recipe_data["name"],
            description=recipe_data.get("description"),
            category=recipe_data.get("category"),
            selling_price=recipe_data["selling_price"],
            total_cost=total_cost,
            actual_margin=margin,
            target_margin=recipe_data["target_margin"],
            prep_time_minutes=recipe_data.get("prep_time_minutes"),
            ingredients=recipe_data.get("ingredients", []),
        ))
    
    return recipes


@router.get("/{recipe_id}", response_model=RecipeOut, summary="Obtener receta por ID")
async def get_recipe(recipe_id: str) -> RecipeOut:
    """Obtiene detalles de una receta específica."""
    if recipe_id not in RECIPES_DB:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Receta {recipe_id} no encontrada",
        )
    
    recipe_data = RECIPES_DB[recipe_id]
    total_cost, _ = calculate_recipe_cost(recipe_data.get("ingredients", []))
    margin = calculate_margin(recipe_data["selling_price"], total_cost)
    
    return RecipeOut(
        id=recipe_data["id"],
        name=recipe_data["name"],
        description=recipe_data.get("description"),
        category=recipe_data.get("category"),
        selling_price=recipe_data["selling_price"],
        total_cost=total_cost,
        actual_margin=margin,
        target_margin=recipe_data["target_margin"],
        prep_time_minutes=recipe_data.get("prep_time_minutes"),
        ingredients=recipe_data.get("ingredients", []),
    )


@router.get("/{recipe_id}/cost-breakdown", response_model=CostBreakdown, summary="Desglose de costos")
async def get_recipe_cost_breakdown(recipe_id: str) -> CostBreakdown:
    """
    **Desglose detallado de costos de una receta.**
    
    Muestra:
    - Costo por ingrediente
    - Porcentaje del costo total
    - Margen actual vs objetivo
    - Precio sugerido para alcanzar margen objetivo
    - Recomendaciones de optimización
    """
    if recipe_id not in RECIPES_DB:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Receta {recipe_id} no encontrada",
        )
    
    recipe_data = RECIPES_DB[recipe_id]
    ingredients = recipe_data.get("ingredients", [])
    
    total_cost, breakdown = calculate_recipe_cost(ingredients)
    selling_price = recipe_data["selling_price"]
    margin = calculate_margin(selling_price, total_cost)
    target_margin = recipe_data["target_margin"]
    suggested = suggest_price(total_cost, target_margin)
    
    # Generar recomendaciones
    recommendations = []
    if margin < target_margin:
        recommendations.append(f"Incrementar precio a ${suggested:.2f} para alcanzar {target_margin}% de margen")
        
        # Encontrar ingredientes más caros
        expensive = sorted(breakdown, key=lambda x: x["percentage"], reverse=True)[:2]
        if expensive:
            rec_text = f"Optimizar costos de: {', '.join([i['name'] for i in expensive])} ({expensive[0]['percentage']:.1f}% del costo)"
            recommendations.append(rec_text)
    
    if margin > target_margin + 10:
        recommendations.append("Margen saludable - considerar mantener o reducir precio para ser más competitivo")
    
    return CostBreakdown(
        recipe_id=recipe_id,
        recipe_name=recipe_data["name"],
        total_cost=total_cost,
        selling_price=selling_price,
        margin_percent=margin,
        target_margin_percent=target_margin,
        is_profitable=margin > 0,
        suggested_price=suggested,
        ingredients_breakdown=breakdown,
        recommendations=recommendations,
    )


@router.post("", response_model=RecipeOut, status_code=status.HTTP_201_CREATED, summary="Crear receta")
async def create_recipe(recipe: RecipeCreate) -> RecipeOut:
    """Crea una nueva receta con sus ingredientes."""
    import uuid
    
    recipe_id = f"recipe-{uuid.uuid4().hex[:8]}"
    
    # Convertir ingredientes a formato interno
    ingredients_data = []
    for ing in recipe.ingredients:
        subtotal = ing.quantity * ing.cost_per_unit
        ingredients_data.append({
            "name": ing.ingredient_name,
            "quantity": ing.quantity,
            "unit": ing.unit_of_measure,
            "cost_per_unit": ing.cost_per_unit,
            "subtotal": round(subtotal, 2),
        })
    
    total_cost, _ = calculate_recipe_cost(ingredients_data)
    margin = calculate_margin(recipe.selling_price, total_cost)
    
    recipe_data = {
        "id": recipe_id,
        "name": recipe.name,
        "description": recipe.description,
        "category": recipe.category,
        "selling_price": recipe.selling_price,
        "target_margin": recipe.target_margin,
        "prep_time_minutes": recipe.prep_time_minutes,
        "ingredients": ingredients_data,
    }
    
    # Guardar en "DB"
    RECIPES_DB[recipe_id] = recipe_data
    
    return RecipeOut(
        id=recipe_id,
        name=recipe.name,
        description=recipe.description,
        category=recipe.category,
        selling_price=recipe.selling_price,
        total_cost=total_cost,
        actual_margin=margin,
        target_margin=recipe.target_margin,
        prep_time_minutes=recipe.prep_time_minutes,
        ingredients=ingredients_data,
    )


@router.delete("/{recipe_id}", summary="Eliminar receta")
async def delete_recipe(recipe_id: str) -> dict:
    """Elimina una receta."""
    if recipe_id not in RECIPES_DB:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Receta {recipe_id} no encontrada",
        )
    
    del RECIPES_DB[recipe_id]
    return {"success": True, "message": f"Receta {recipe_id} eliminada"}
