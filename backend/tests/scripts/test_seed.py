"""Prueba el script de seed (RF-05.2) contra SQLite en memoria, con el
catalogo de categorias cargado como lo hace la migracion 0004."""

import os
import subprocess
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.categorias.models import Categoria
from app.db.base import Base
from app.eventos.factory import EventoFactory
from app.eventos.models import Evento, Lugar, OrigenEvento
from app.eventos.repository import SQLAlchemyEventoRepository
from app.eventos.schemas import BusquedaEventosParams
from scripts.seed import EVENTOS, sembrar

BUENOS_AIRES = ZoneInfo('America/Argentina/Buenos_Aires')
HOY = date(2026, 11, 20)
AHORA = datetime(2026, 11, 20, 12, 0, tzinfo=timezone.utc)
SLUGS = (
    'bar',
    'recital',
    'teatro',
    'cine',
    'deportivo',
    'museo',
    'gastronomia',
    'feria',
    'taller',
    'aire-libre',
    'otro',
)


@pytest.fixture
async def session_factory():
    engine = create_async_engine('sqlite+aiosqlite:///:memory:')
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        session.add_all(Categoria(slug=s, nombre=s) for s in SLUGS)
        await session.commit()

    yield factory

    await engine.dispose()


def _factory() -> EventoFactory:
    return EventoFactory(BUENOS_AIRES, reloj=lambda: AHORA)


async def _sembrar(session_factory, reset: bool = False) -> int:
    async with session_factory() as session:
        cargados = await sembrar(
            session, _factory(), HOY, BUENOS_AIRES, reset=reset
        )
        await session.commit()
    return cargados


async def _contar(session_factory, modelo) -> int:
    async with session_factory() as session:
        return await session.scalar(select(func.count()).select_from(modelo))


async def test_carga_eventos_de_seed_sin_organizador(session_factory):
    cargados = await _sembrar(session_factory)

    assert cargados == len(EVENTOS)
    async with session_factory() as session:
        eventos = (await session.execute(select(Evento))).scalars().all()
    assert {e.origen for e in eventos} == {OrigenEvento.SEED_EQUIPO}
    assert {e.id_organizador for e in eventos} == {None}
    assert all(e.categorias for e in eventos)


async def test_usa_todas_las_categorias_del_catalogo(session_factory):
    await _sembrar(session_factory)

    async with session_factory() as session:
        eventos = (await session.execute(select(Evento))).scalars().all()
    assert {c.slug for e in eventos for c in e.categorias} == set(SLUGS)


async def test_los_eventos_publicados_aparecen_en_la_busqueda(
    session_factory,
):
    await _sembrar(session_factory)

    async with session_factory() as session:
        _, total = await SQLAlchemyEventoRepository(session).buscar(
            BusquedaEventosParams(limit=100), AHORA
        )
    cancelados = sum(1 for seed in EVENTOS if seed.cancelado)
    assert cancelados >= 1
    assert total == len(EVENTOS) - cancelados


async def test_no_duplica_si_ya_hay_seed(session_factory):
    await _sembrar(session_factory)

    assert await _sembrar(session_factory) == 0
    assert await _contar(session_factory, Evento) == len(EVENTOS)


async def test_reset_borra_el_seed_y_vuelve_a_cargar(session_factory):
    await _sembrar(session_factory)

    assert await _sembrar(session_factory, reset=True) == len(EVENTOS)
    assert await _contar(session_factory, Evento) == len(EVENTOS)
    assert await _contar(session_factory, Lugar) == len(EVENTOS)


async def test_reset_no_toca_eventos_de_organizadores(session_factory):
    async with session_factory() as session:
        propio = _factory().crear_seed(
            titulo='Propio',
            descripcion='x',
            fecha_inicio=AHORA,
            fecha_fin=None,
            lugar=Lugar(latitud=-34.6, longitud=-58.4),
            categorias=[],
        )
        propio.origen = OrigenEvento.CARGA_ORGANIZADOR
        session.add(propio)
        await session.commit()

    await _sembrar(session_factory, reset=True)

    async with session_factory() as session:
        restantes = await session.scalar(
            select(func.count())
            .select_from(Evento)
            .where(Evento.origen == OrigenEvento.CARGA_ORGANIZADOR)
        )
    assert restantes == 1


async def test_falla_si_faltan_categorias():
    engine = create_async_engine('sqlite+aiosqlite:///:memory:')
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with async_sessionmaker(engine)() as session:
        with pytest.raises(RuntimeError, match='alembic upgrade head'):
            await sembrar(session, _factory(), HOY, BUENOS_AIRES)
    await engine.dispose()


def test_hay_eventos_despues_de_medianoche_y_cancelados():
    assert any(seed.hora.hour < 6 for seed in EVENTOS)
    assert any(seed.cancelado for seed in EVENTOS)
    assert all(seed.cancelado or seed.dias >= 1 for seed in EVENTOS), (
        'los eventos visibles tienen que quedar a futuro'
    )


async def test_el_script_corre_de_punta_a_punta(tmp_path: Path):
    """Corre el script como lo haria alguien del equipo, en un proceso
    aparte: detecta errores de arranque (imports, modelos sin registrar)
    que los tests en proceso no ven."""
    url = f'sqlite+aiosqlite:///{tmp_path / "seed.db"}'
    engine = create_async_engine(url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with async_sessionmaker(engine)() as session:
        session.add_all(Categoria(slug=s, nombre=s) for s in SLUGS)
        await session.commit()
    await engine.dispose()

    backend = Path(__file__).resolve().parents[2]
    resultado = subprocess.run(
        [sys.executable, '-m', 'scripts.seed'],
        cwd=backend,
        env={**os.environ, 'DATABASE_URL': url},
        capture_output=True,
        text=True,
        check=False,
    )

    assert resultado.returncode == 0, resultado.stderr
    assert f'Se cargaron {len(EVENTOS)} eventos' in resultado.stdout
