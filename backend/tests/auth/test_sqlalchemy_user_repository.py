"""Unico test del modulo de auth que toca una base de datos real (SQLite en
memoria via aiosqlite, admitido por RNF-05.2 solo para tests). Prueba
SQLAlchemyUserRepository en aislamiento, sin involucrar Auth ni las
estrategias -- exactamente la separacion que habilita el DIP del diseno."""

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.auth.repository import SQLAlchemyUserRepository
from app.db.base import Base
from app.models.usuario import RolEnum


@pytest.fixture
async def sqlite_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


async def test_create_and_get_by_email(sqlite_session):
    repo = SQLAlchemyUserRepository(sqlite_session)

    creado = await repo.create(
        email="a@a.com", password_hash="hash", nombre="Ana", rol=RolEnum.DEMANDANTE
    )
    await sqlite_session.commit()

    encontrado = await repo.get_by_email("a@a.com")

    assert encontrado is not None
    assert encontrado.id == creado.id
    assert encontrado.rol == RolEnum.DEMANDANTE


async def test_get_by_email_returns_none_when_missing(sqlite_session):
    repo = SQLAlchemyUserRepository(sqlite_session)

    assert await repo.get_by_email("nadie@a.com") is None


async def test_get_by_id_returns_none_when_missing(sqlite_session):
    from uuid import uuid4

    repo = SQLAlchemyUserRepository(sqlite_session)

    assert await repo.get_by_id(uuid4()) is None
