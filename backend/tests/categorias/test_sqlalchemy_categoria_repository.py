"""Prueba SQLAlchemyCategoriaRepository contra SQLite en memoria (admitido
por RNF-05.2 solo para tests)."""

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.categorias.models import Categoria
from app.categorias.repository import SQLAlchemyCategoriaRepository
from app.db.base import Base


@pytest.fixture
async def session_factory():
    engine = create_async_engine('sqlite+aiosqlite:///:memory:')
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        session.add_all([
            Categoria(slug='teatro', nombre='Teatro'),
            Categoria(slug='bar', nombre='Bar'),
            Categoria(slug='cine', nombre='Cine', activa=False),
        ])
        await session.commit()

    yield factory

    await engine.dispose()


async def test_list_activas_excluye_inactivas_y_ordena_por_nombre(
    session_factory,
):
    async with session_factory() as session:
        categorias = await SQLAlchemyCategoriaRepository(
            session
        ).list_activas()

    assert [c.slug for c in categorias] == ['bar', 'teatro']


async def test_get_activas_by_slugs_ignora_inexistentes_e_inactivas(
    session_factory,
):
    async with session_factory() as session:
        categorias = await SQLAlchemyCategoriaRepository(
            session
        ).get_activas_by_slugs(['bar', 'cine', 'inexistente'])

    assert [c.slug for c in categorias] == ['bar']


async def test_get_activas_by_slugs_vacio_devuelve_lista_vacia(
    session_factory,
):
    async with session_factory() as session:
        repo = SQLAlchemyCategoriaRepository(session)
        assert await repo.get_activas_by_slugs([]) == []
