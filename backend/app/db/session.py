from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings

_settings = get_settings()

engine = create_async_engine(_settings.database_url, echo=False)

async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provider de FastAPI: una sesion por request (FastAPI cachea el
    resultado de un mismo Depends dentro de la misma request, asi que todos
    los repositorios de una request comparten la misma sesion/transaccion).
    Commit al finalizar el endpoint sin errores; rollback si algo lanzo."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
