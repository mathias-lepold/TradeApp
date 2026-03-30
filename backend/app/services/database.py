"""
Service: DatabaseService
Async PostgreSQL-Verbindung via SQLAlchemy 2.0 + asyncpg.
"""
from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings


class Base(DeclarativeBase):
    """Gemeinsame Basisklasse für alle SQLAlchemy-Modelle."""
    pass


# Engine und Session-Factory werden beim Import erstellt
def _create_engine() -> AsyncEngine:
    settings = get_settings()
    return create_async_engine(
        settings.database_url,
        echo=settings.debug,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
    )


engine: AsyncEngine = _create_engine()

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI-Dependency für Datenbankzugriff.

    Verwendung in Routen:
        @app.get("/...")
        async def route(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_tables() -> None:
    """Erstellt alle Tabellen (für Dev/Test). Prod: Alembic-Migrationen."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def health_check() -> bool:
    """Prüft ob die Datenbankverbindung funktioniert."""
    try:
        async with engine.connect() as conn:
            await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
        return True
    except Exception:
        return False
