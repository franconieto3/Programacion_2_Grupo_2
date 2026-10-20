"""Prueba SQLAlchemyAdministradorRepository contra SQLite en memoria (admitido
por RNF-05.2 solo para tests), igual que el repositorio de organizadores."""

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.administradores.models import Administrador
from app.administradores.repository import SQLAlchemyAdministradorRepository
from app.db.base import Base
from app.models.usuario import Usuario


@pytest.fixture
async def session_factory():
    engine = create_async_engine('sqlite+aiosqlite:///:memory:')
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield async_sessionmaker(engine, expire_on_commit=False)

    await engine.dispose()


@pytest.fixture
async def usuario(session_factory) -> Usuario:
    async with session_factory() as session:
        usuario = Usuario(nombre='Ana', apellido='Gomez', email='a@a.com')
        session.add(usuario)
        await session.commit()
    return usuario


async def test_get_by_usuario_id_de_un_administrador(session_factory, usuario):
    async with session_factory() as session:
        session.add(Administrador(id_usuario=usuario.id))
        await session.commit()

    async with session_factory() as session:
        admin = await SQLAlchemyAdministradorRepository(
            session
        ).get_by_usuario_id(usuario.id)

    assert admin is not None
    assert admin.id_usuario == usuario.id
    assert admin.fecha_alta is not None


async def test_get_by_usuario_id_sin_perfil_devuelve_none(
    session_factory, usuario
):
    async with session_factory() as session:
        repo = SQLAlchemyAdministradorRepository(session)
        assert await repo.get_by_usuario_id(usuario.id) is None
