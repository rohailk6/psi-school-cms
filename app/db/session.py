from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings


# The engine is the actual connection to PostgreSQL
# Think of it like opening a phone line to the database
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,    # test connection before using it
    echo=settings.DEBUG,   # print SQL queries in terminal when DEBUG=True
)

# Session factory — creates individual sessions (conversations with the DB)
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


# Base class — all your database models will inherit from this
class Base(DeclarativeBase):
    pass # ← Alembic needs this to detect all your models


# Dependency — FastAPI calls this automatically for any endpoint that needs the DB
# It opens a session, gives it to your endpoint, then closes it when done
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session          # hand the session to the endpoint
            await session.commit() # save changes if no error
        except Exception:
            await session.rollback() # undo changes if something went wrong
            raise
        finally:
            await session.close()  # always close the session