"""PRAXIS Database Configuration.

Handles connections to Postgres (production) or local SQLite (development/testing).
"""

import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from api.models import Base

# Determine database URL.
# If Postgres is not configured, fallback to local SQLite (requires aiosqlite).
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    # Use SQLite relative to workspace root
    DATABASE_URL = "sqlite+aiosqlite:///praxis.db"
else:
    if DATABASE_URL.startswith("postgresql://"):
        # SQLAlchemy requires postgresql+asyncpg for async execution
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
    # asyncpg takes ssl=, not the psycopg2-style sslmode= query param
    DATABASE_URL = DATABASE_URL.replace("sslmode=require", "ssl=require")

# Create async engine
# For SQLite, we turn off pool check_same_thread because we handle session scopes
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)

# Async session maker
async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db():
    """Initialise database schema (creates tables if they do not exist)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    """Dependency for retrieving DB session."""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()
