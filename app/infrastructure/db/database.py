"""Configuración de base de datos SQLAlchemy."""
from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings

settings = get_settings()

# Crear engine asíncrono
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DB_ECHO,
    future=True,
)

# Session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Clase base para modelos SQLAlchemy."""
    
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency para obtener sesión de DB."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Inicializa la base de datos (crea tablas)."""
    async with engine.begin() as conn:
        # Importar todos los modelos para registrarlos
        from app.domain import models  # noqa: F401
        await conn.run_sync(Base.metadata.create_all)
