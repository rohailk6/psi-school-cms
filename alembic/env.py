from __future__ import annotations

import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# ── This adds your backend/ folder to the Python path ────────────────────────
# Without this, Alembic can't find your app when it runs
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# ── Import your settings and Base ────────────────────────────────────────────
from app.core.config import settings
from app.db.session import Base

# ── Import ALL models so Alembic can detect them ─────────────────────────────
# This is critical — if you don't import a model here,
# Alembic won't know it exists and won't create its table
import app.models

# ── Standard Alembic setup ───────────────────────────────────────────────────
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Tell Alembic where to find your table definitions
target_metadata = Base.metadata

# Override the database URL from your app settings
# This way you only define the URL in one place (.env)
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL_SYNC)


def run_migrations_offline() -> None:
    """
    Run migrations without a live DB connection.
    Useful for generating SQL scripts to review before applying.
    """
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
    """
    Run migrations with a live DB connection.
    This is what you use normally — it actually creates the tables.
    """
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


# Alembic decides which mode to use automatically
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()