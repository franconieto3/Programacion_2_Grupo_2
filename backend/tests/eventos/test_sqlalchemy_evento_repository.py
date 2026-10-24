"""Prueba SQLAlchemyEventoRepository contra SQLite en memoria (admitido
por RNF-05.2 solo para tests): regla de visibilidad, orden y paginacion de
la busqueda, y el alta y la lectura por id. Los filtros de
app/eventos/filtros/ tienen sus propios tests."""

from datetime import datetime, timedelta, timezone
from uuid import uuid4
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.categorias.models import Categoria
from app.db.base import Base
from app.eventos.models import EstadoEvento, Evento, Lugar, OrigenEvento
from app.eventos.repository import SQLAlchemyEventoRepository
from app.eventos.schemas import BusquedaEventosParams

AHORA = datetime(2026, 11, 20, 12, 0, tzinfo=timezone.utc)
BUENOS_AIRES = ZoneInfo('America/Argentina/Buenos_Aires')


@pytest.fixture
async def session_factory():
    engine = create_async_engine('sqlite+aiosqlite:///:memory:')
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield async_sessionmaker(engine, expire_on_commit=False)

    await engine.dispose()


def _evento(
    titulo: str,
    inicio: datetime,
    fin: datetime | None = None,
    estado: EstadoEvento = EstadoEvento.PUBLICADO,
    categorias: list[Categoria] | None = None,
) -> Evento:
    evento = Evento(
        titulo=titulo,
        descripcion='Descripcion',
        estado=estado,
        origen=OrigenEvento.SEED_EQUIPO,
        lugar=Lugar(nombre='Plaza', latitud=-34.6, longitud=-58.4),
        categorias=categorias or [],
    )
    evento.programar(inicio, fin, BUENOS_AIRES)
    return evento


async def _guardar(session_factory, *eventos: Evento) -> None:
    async with session_factory() as session:
        session.add_all(eventos)
        await session.commit()


async def _buscar(session_factory, **params) -> tuple[list[Evento], int]:
    async with session_factory() as session:
        return await SQLAlchemyEventoRepository(session).buscar(
            BusquedaEventosParams(**params), AHORA
        )


async def test_solo_devuelve_eventos_publicados(session_factory):
    manana = AHORA + timedelta(days=1)
    await _guardar(
        session_factory,
        _evento('Publicado', manana),
        _evento('Borrador', manana, estado=EstadoEvento.BORRADOR),
        _evento('Cancelado', manana, estado=EstadoEvento.CANCELADO),
        _evento('Oculto', manana, estado=EstadoEvento.OCULTO),
    )

    eventos, total = await _buscar(session_factory)

    assert [e.titulo for e in eventos] == ['Publicado']
    assert total == 1


async def test_sin_fecha_fin_se_muestra_hasta_que_empieza(session_factory):
    await _guardar(
        session_factory,
        _evento('Empieza en una hora', AHORA + timedelta(hours=1)),
        _evento('Empezo hace una hora', AHORA - timedelta(hours=1)),
    )

    eventos, _ = await _buscar(session_factory)

    assert [e.titulo for e in eventos] == ['Empieza en una hora']


async def test_con_fecha_fin_se_muestra_hasta_que_termina(session_factory):
    await _guardar(
        session_factory,
        _evento(
            'En curso',
            AHORA - timedelta(hours=1),
            fin=AHORA + timedelta(hours=1),
        ),
        _evento(
            'Terminado',
            AHORA - timedelta(hours=3),
            fin=AHORA - timedelta(hours=1),
        ),
    )

    eventos, _ = await _buscar(session_factory)

    assert [e.titulo for e in eventos] == ['En curso']


async def test_ordena_por_fecha_de_inicio_y_pagina(session_factory):
    await _guardar(
        session_factory,
        *[
            _evento(f'Evento {dia}', AHORA + timedelta(days=dia))
            for dia in (3, 1, 2)
        ],
    )

    eventos, total = await _buscar(session_factory, limit=2, offset=1)

    assert [e.titulo for e in eventos] == ['Evento 2', 'Evento 3']
    assert total == 3


async def test_carga_lugar_y_categorias(session_factory):
    bar = Categoria(slug='bar', nombre='Bar')
    await _guardar(
        session_factory,
        _evento('Con categoria', AHORA + timedelta(days=1), categorias=[bar]),
    )

    eventos, _ = await _buscar(session_factory)

    assert eventos[0].lugar.nombre == 'Plaza'
    assert [c.slug for c in eventos[0].categorias] == ['bar']


async def test_add_asigna_id_y_get_by_id_lo_recupera(session_factory):
    bar = Categoria(slug='bar', nombre='Bar')
    async with session_factory() as session:
        evento = await SQLAlchemyEventoRepository(session).add(
            _evento('Nuevo', AHORA + timedelta(days=1), categorias=[bar])
        )
        await session.commit()
        id_evento = evento.id_evento

    assert id_evento is not None
    async with session_factory() as session:
        leido = await SQLAlchemyEventoRepository(session).get_by_id(id_evento)

    assert leido.titulo == 'Nuevo'
    assert leido.lugar.nombre == 'Plaza'
    assert [c.slug for c in leido.categorias] == ['bar']


async def test_get_by_id_devuelve_eventos_en_cualquier_estado(session_factory):
    oculto = _evento(
        'Oculto', AHORA + timedelta(days=1), estado=EstadoEvento.OCULTO
    )
    await _guardar(session_factory, oculto)

    async with session_factory() as session:
        leido = await SQLAlchemyEventoRepository(session).get_by_id(
            oculto.id_evento
        )

    assert leido.estado == EstadoEvento.OCULTO


async def test_get_by_id_inexistente_devuelve_none(session_factory):
    async with session_factory() as session:
        leido = await SQLAlchemyEventoRepository(session).get_by_id(uuid4())

    assert leido is None
