"""Prueba los filtros de GET /eventos (fechas, horario y categorias) contra
SQLite en memoria, usando SQLAlchemyEventoRepository.buscar. Zona horaria
por defecto: America/Argentina/Buenos_Aires (UTC-3, sin horario de verano)."""

from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest
from pydantic import ValidationError
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


def _local(dia: int, hora: int, minuto: int = 0) -> datetime:
    """Instante de noviembre de 2026 dado en hora local, en UTC (como se
    guarda en la base)."""
    return datetime(
        2026, 11, dia, hora, minuto, tzinfo=BUENOS_AIRES
    ).astimezone(timezone.utc)


def _evento(
    titulo: str,
    inicio: datetime,
    categorias: list[Categoria] | None = None,
    latitud: float = -34.6,
) -> Evento:
    evento = Evento(
        titulo=titulo,
        descripcion='Descripcion',
        estado=EstadoEvento.PUBLICADO,
        origen=OrigenEvento.SEED_EQUIPO,
        lugar=Lugar(nombre='Plaza', latitud=latitud, longitud=-58.4),
        categorias=categorias or [],
    )
    evento.programar(inicio, None, BUENOS_AIRES)
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


def _titulos(eventos: list[Evento]) -> list[str]:
    return [e.titulo for e in eventos]


# ---------------------------------------------------------------- fechas


async def test_fechas_sin_desde_ni_hasta_no_filtra(session_factory):
    await _guardar(
        session_factory,
        _evento('A', _local(25, 10)),
        _evento('B', _local(28, 10)),
    )

    eventos, total = await _buscar(session_factory)

    assert _titulos(eventos) == ['A', 'B']
    assert total == 2


async def test_fechas_desde_incluye_el_primer_instante_local_del_dia(
    session_factory,
):
    # 00:00 locales del 25 = 03:00 UTC; un minuto antes todavia es el 24.
    await _guardar(
        session_factory,
        _evento('Justo antes', _local(24, 23, 59)),
        _evento('Justo en el limite', _local(25, 0, 0)),
    )

    eventos, _ = await _buscar(session_factory, desde=date(2026, 11, 25))

    assert _titulos(eventos) == ['Justo en el limite']


async def test_fechas_hasta_es_inclusivo_hasta_el_fin_del_dia_local(
    session_factory,
):
    await _guardar(
        session_factory,
        _evento('Ultimo minuto del 25', _local(25, 23, 59)),
        _evento('Primer instante del 26', _local(26, 0, 0)),
    )

    eventos, _ = await _buscar(session_factory, hasta=date(2026, 11, 25))

    assert _titulos(eventos) == ['Ultimo minuto del 25']


async def test_fechas_usa_el_dia_local_y_no_el_dia_utc(session_factory):
    # 23:30 locales del 25 son las 02:30 UTC del 26: el dia UTC no manda.
    await _guardar(
        session_factory,
        _evento('Noche del 25', _local(25, 23, 30)),
        _evento('Madrugada del 26', _local(26, 0, 30)),
    )

    eventos, _ = await _buscar(
        session_factory, desde=date(2026, 11, 25), hasta=date(2026, 11, 25)
    )

    assert _titulos(eventos) == ['Noche del 25']


async def test_fechas_solo_desde_deja_abierto_el_extremo_superior(
    session_factory,
):
    await _guardar(
        session_factory,
        _evento('Antes', _local(22, 10)),
        _evento('Despues', _local(30, 10)),
    )

    eventos, _ = await _buscar(session_factory, desde=date(2026, 11, 25))

    assert _titulos(eventos) == ['Despues']


async def test_fechas_solo_hasta_deja_abierto_el_extremo_inferior(
    session_factory,
):
    await _guardar(
        session_factory,
        _evento('Antes', _local(22, 10)),
        _evento('Despues', _local(30, 10)),
    )

    eventos, _ = await _buscar(session_factory, hasta=date(2026, 11, 25))

    assert _titulos(eventos) == ['Antes']


async def test_fechas_rango_de_varios_dias(session_factory):
    await _guardar(
        session_factory,
        _evento('Fuera antes', _local(21, 10)),
        _evento('Dentro 1', _local(23, 10)),
        _evento('Dentro 2', _local(25, 22)),
        _evento('Fuera despues', _local(26, 10)),
    )

    eventos, total = await _buscar(
        session_factory, desde=date(2026, 11, 22), hasta=date(2026, 11, 25)
    )

    assert _titulos(eventos) == ['Dentro 1', 'Dentro 2']
    assert total == 2


def test_fechas_desde_igual_a_hasta_es_valido():
    BusquedaEventosParams(desde=date(2026, 11, 25), hasta=date(2026, 11, 25))


def test_fechas_desde_posterior_a_hasta_es_invalido():
    with pytest.raises(ValidationError, match='desde no puede ser posterior'):
        BusquedaEventosParams(
            desde=date(2026, 11, 30), hasta=date(2026, 11, 20)
        )



# --------------------------------------------------------------- horario


async def test_horario_sin_extremos_no_filtra(session_factory):
    await _guardar(
        session_factory,
        _evento('Manana', _local(25, 9)),
        _evento('Noche', _local(25, 23)),
    )

    eventos, _ = await _buscar(session_factory)

    assert _titulos(eventos) == ['Manana', 'Noche']


async def test_horario_rango_normal_con_bordes_inclusivos(session_factory):
    await _guardar(
        session_factory,
        _evento('19:59', _local(25, 19, 59)),
        _evento('20:00', _local(25, 20, 0)),
        _evento('22:00', _local(25, 22, 0)),
        _evento('22:01', _local(25, 22, 1)),
    )

    eventos, _ = await _buscar(
        session_factory, hora_desde=time(20, 0), hora_hasta=time(22, 0)
    )

    assert _titulos(eventos) == ['20:00', '22:00']


async def test_horario_usa_la_hora_local_y_no_la_utc(session_factory):
    # 21:00 locales son las 00:00 UTC del dia siguiente.
    await _guardar(session_factory, _evento('21 local', _local(25, 21)))

    eventos, _ = await _buscar(
        session_factory, hora_desde=time(20, 0), hora_hasta=time(22, 0)
    )

    assert _titulos(eventos) == ['21 local']


async def test_horario_que_cruza_la_medianoche(session_factory):
    await _guardar(
        session_factory,
        _evento('21:59', _local(25, 21, 59)),
        _evento('22:00', _local(25, 22, 0)),
        _evento('23:30', _local(25, 23, 30)),
        _evento('00:00', _local(26, 0, 0)),
        _evento('02:00', _local(26, 2, 0)),
        _evento('02:01', _local(26, 2, 1)),
        _evento('12:00', _local(26, 12, 0)),
    )

    eventos, total = await _buscar(
        session_factory, hora_desde=time(22, 0), hora_hasta=time(2, 0)
    )

    assert sorted(_titulos(eventos)) == ['00:00', '02:00', '22:00', '23:30']
    assert total == 4


async def test_horario_solo_desde_deja_abierto_el_extremo_superior(
    session_factory,
):
    await _guardar(
        session_factory,
        _evento('Manana', _local(25, 9)),
        _evento('Noche', _local(25, 23)),
    )

    eventos, _ = await _buscar(session_factory, hora_desde=time(20, 0))

    assert _titulos(eventos) == ['Noche']


async def test_horario_solo_hasta_deja_abierto_el_extremo_inferior(
    session_factory,
):
    await _guardar(
        session_factory,
        _evento('Manana', _local(25, 9)),
        _evento('Noche', _local(25, 23)),
    )

    eventos, _ = await _buscar(session_factory, hora_hasta=time(12, 0))

    assert _titulos(eventos) == ['Manana']



# ------------------------------------------------------------ categorias


def _categoria(slug: str) -> Categoria:
    return Categoria(slug=slug, nombre=slug.capitalize())


@pytest.fixture
def cats():
    return {s: _categoria(s) for s in ('bar', 'teatro', 'recital')}


async def test_categorias_sin_filtro_incluye_eventos_sin_categoria(
    session_factory, cats
):
    await _guardar(
        session_factory,
        _evento('Con bar', _local(25, 10), [cats['bar']]),
        _evento('Sin categoria', _local(26, 10)),
    )

    eventos, total = await _buscar(session_factory)

    assert _titulos(eventos) == ['Con bar', 'Sin categoria']
    assert total == 2


async def test_categorias_una_sola(session_factory, cats):
    await _guardar(
        session_factory,
        _evento('Bar', _local(25, 10), [cats['bar']]),
        _evento('Teatro', _local(26, 10), [cats['teatro']]),
        _evento('Sin categoria', _local(27, 10)),
    )

    eventos, total = await _buscar(session_factory, categorias=['bar'])

    assert _titulos(eventos) == ['Bar']
    assert total == 1


async def test_categorias_varias_coinciden_con_al_menos_una(
    session_factory, cats
):
    await _guardar(
        session_factory,
        _evento('Bar', _local(25, 10), [cats['bar']]),
        _evento('Teatro', _local(26, 10), [cats['teatro']]),
        _evento('Recital', _local(27, 10), [cats['recital']]),
    )

    eventos, _ = await _buscar(session_factory, categorias=['bar', 'teatro'])

    assert _titulos(eventos) == ['Bar', 'Teatro']


async def test_categorias_evento_con_varias_pedidas_no_se_duplica(
    session_factory, cats
):
    await _guardar(
        session_factory,
        _evento('Bar y teatro', _local(25, 10), [cats['bar'], cats['teatro']]),
        _evento('Solo bar', _local(26, 10), [cats['bar']]),
    )

    eventos, total = await _buscar(
        session_factory, categorias=['bar', 'teatro']
    )

    assert _titulos(eventos) == ['Bar y teatro', 'Solo bar']
    assert total == 2


async def test_categorias_slug_inexistente_no_devuelve_nada(
    session_factory, cats
):
    await _guardar(
        session_factory, _evento('Bar', _local(25, 10), [cats['bar']])
    )

    eventos, total = await _buscar(session_factory, categorias=['no-existe'])

    assert eventos == []
    assert total == 0


async def test_categorias_slug_inexistente_junto_a_uno_valido(
    session_factory, cats
):
    await _guardar(
        session_factory, _evento('Bar', _local(25, 10), [cats['bar']])
    )

    eventos, _ = await _buscar(
        session_factory, categorias=['no-existe', 'bar']
    )

    assert _titulos(eventos) == ['Bar']



# ----------------------------------------------- combinados y determinismo


async def test_filtros_combinados(session_factory, cats):
    await _guardar(
        session_factory,
        _evento('Cumple todo', _local(25, 21), [cats['bar']]),
        _evento('Fecha fuera', _local(29, 21), [cats['bar']]),
        _evento('Hora fuera', _local(25, 10), [cats['bar']]),
        _evento('Categoria fuera', _local(25, 21), [cats['teatro']]),
        _evento(
            'Viewport fuera', _local(25, 21), [cats['bar']], latitud=-31.0
        ),
    )

    eventos, total = await _buscar(
        session_factory,
        desde=date(2026, 11, 24),
        hasta=date(2026, 11, 26),
        hora_desde=time(20, 0),
        hora_hasta=time(23, 0),
        categorias=['bar'],
        lat_min=-35,
        lat_max=-34,
        lng_min=-59,
        lng_max=-58,
    )

    assert _titulos(eventos) == ['Cumple todo']
    assert total == 1


async def test_mismos_parametros_dan_siempre_el_mismo_orden(
    session_factory, cats
):
    # Mismo instante de inicio: el id desempata y el orden es estable.
    mismo_instante = _local(25, 21)
    await _guardar(
        session_factory,
        *[_evento(f'E{i}', mismo_instante, [cats['bar']]) for i in range(8)],
    )
    params = {'categorias': ['bar'], 'hora_desde': time(20, 0)}

    corridas = [
        _titulos((await _buscar(session_factory, **params))[0])
        for _ in range(3)
    ]

    assert corridas[0] == corridas[1] == corridas[2]
    assert len(corridas[0]) == 8


async def test_paginas_con_filtros_no_repiten_ni_pierden_eventos(
    session_factory, cats
):
    await _guardar(
        session_factory,
        *[
            _evento(
                f'E{i}',
                _local(25, 21) + timedelta(minutes=i % 3),
                [cats['bar'], cats['teatro']],
            )
            for i in range(7)
        ],
        _evento('Otra categoria', _local(25, 21), [cats['recital']]),
    )
    filtros = {'categorias': ['bar', 'teatro'], 'hora_desde': time(20, 0)}

    vistos: list[str] = []
    for offset in (0, 3, 6):
        pagina, total = await _buscar(
            session_factory, **filtros, limit=3, offset=offset
        )
        assert total == 7
        vistos += _titulos(pagina)

    assert len(vistos) == 7
    assert len(set(vistos)) == 7
    assert 'Otra categoria' not in vistos