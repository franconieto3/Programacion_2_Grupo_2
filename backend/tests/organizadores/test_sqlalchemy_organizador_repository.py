"""Prueba SQLAlchemyOrganizadorRepository contra SQLite en memoria (admitido
por RNF-05.2 solo para tests), igual que el repositorio de usuarios."""

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.base import Base
from app.models.usuario import Usuario
from app.organizadores.exceptions import SolicitudYaExistenteError
from app.organizadores.models import EstadoOrganizador, Organizador
from app.organizadores.repository import SQLAlchemyOrganizadorRepository


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


def _organizador(usuario: Usuario) -> Organizador:
    return Organizador(
        id_usuario=usuario.id,
        nombre_publico='Bar Los Pinos',
        descripcion='Musica en vivo',
        estado=EstadoOrganizador.PENDIENTE,
    )


async def test_add_y_get_by_usuario_id(session_factory, usuario):
    async with session_factory() as session:
        creado = await SQLAlchemyOrganizadorRepository(session).add(
            _organizador(usuario)
        )
        await session.commit()

    async with session_factory() as session:
        encontrado = await SQLAlchemyOrganizadorRepository(
            session
        ).get_by_usuario_id(usuario.id)

    assert encontrado is not None
    assert encontrado.id_organizador == creado.id_organizador
    assert encontrado.estado == EstadoOrganizador.PENDIENTE
    assert encontrado.fecha_creacion is not None


async def test_get_by_usuario_id_sin_perfil_devuelve_none(
    session_factory, usuario
):
    async with session_factory() as session:
        repo = SQLAlchemyOrganizadorRepository(session)
        assert await repo.get_by_usuario_id(usuario.id) is None


async def test_add_duplicado_lanza_solicitud_ya_existente(
    session_factory, usuario
):
    async with session_factory() as session:
        await SQLAlchemyOrganizadorRepository(session).add(
            _organizador(usuario)
        )
        await session.commit()

    async with session_factory() as session:
        with pytest.raises(SolicitudYaExistenteError):
            await SQLAlchemyOrganizadorRepository(session).add(
                _organizador(usuario)
            )


async def test_list_by_estado_filtra_por_estado(session_factory, usuario):
    async with session_factory() as session:
        otro = Usuario(nombre='Beto', apellido='Diaz', email='b@b.com')
        session.add(otro)
        await session.flush()

        repo = SQLAlchemyOrganizadorRepository(session)
        pendiente = await repo.add(_organizador(usuario))
        aprobado = _organizador(otro)
        aprobado.estado = EstadoOrganizador.APROBADO
        await repo.add(aprobado)
        await session.commit()

    async with session_factory() as session:
        repo = SQLAlchemyOrganizadorRepository(session)
        pendientes = await repo.list_by_estado(EstadoOrganizador.PENDIENTE)
        suspendidos = await repo.list_by_estado(EstadoOrganizador.SUSPENDIDO)

    assert [o.id_organizador for o in pendientes] == [pendiente.id_organizador]
    assert suspendidos == []
