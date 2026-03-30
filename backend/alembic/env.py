"""Alembic Migration Environment."""
from __future__ import annotations

import os
import re
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# Alembic Config-Objekt
config = context.config

# Python-Logging aus alembic.ini einrichten
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# DATABASE_URL aus .env lesen und asyncpg → psycopg2 umschreiben
# (Alembic benötigt einen synchronen Treiber)
db_url = os.environ.get("DATABASE_URL", config.get_main_option("sqlalchemy.url"))
sync_url = re.sub(r"postgresql\+asyncpg://", "postgresql+psycopg2://", db_url)
config.set_main_option("sqlalchemy.url", sync_url)

# Alle ORM-Modelle importieren → Metadaten registrieren
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.services.database import Base  # noqa: E402
import app.models  # noqa: E402 — importiert alle Modelle

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Offline-Modus: SQL-Skript generieren ohne DB-Verbindung."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Online-Modus: direkte DB-Verbindung."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
