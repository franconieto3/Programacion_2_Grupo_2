"""Carga eventos de ejemplo del equipo (RF-05.2): origen SEED_EQUIPO y sin
organizador, creados con EventoFactory.crear_seed.

Estan repartidos en varias zonas (barrios de CABA, GBA y otras ciudades),
fechas, horarios (incluidos algunos despues de medianoche) y categorias, para
poder probar a mano los filtros de la busqueda. Las fechas son relativas al
dia en que se corre el script, asi que los eventos siempre quedan a futuro.

Uso, desde backend/ y con la base migrada (alembic upgrade head):

    poetry run python -m scripts.seed           # carga si no hay seed
    poetry run python -m scripts.seed --reset   # borra el seed y recarga
"""

import argparse
import asyncio
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

# Registra todos los modelos en Base.metadata (como migrations/env.py): sin
# esto SQLAlchemy no resuelve la FK de eventos hacia organizadores.
import app.models  # noqa: F401
from app.categorias.models import Categoria
from app.categorias.repository import SQLAlchemyCategoriaRepository
from app.core.config import get_settings
from app.eventos.factory import EventoFactory
from app.eventos.models import Evento, Lugar, OrigenEvento
from app.eventos.repository import SQLAlchemyEventoRepository


@dataclass(frozen=True)
class EventoSeed:
    """`dias` cuenta desde hoy y `hora` es hora local (Settings.zona_horaria).
    Sin `duracion_horas`, el evento no tiene fecha de fin."""

    titulo: str
    descripcion: str
    lugar: str
    direccion: str
    latitud: float
    longitud: float
    dias: int
    hora: time
    duracion_horas: float | None
    categorias: tuple[str, ...]
    precio: Decimal | None = None
    cancelado: bool = False


# fmt: off
# Formato compacto a mano: una fila de datos por evento se lee mejor que un
# argumento por linea.
EVENTOS: tuple[EventoSeed, ...] = (
    # --- CABA ---
    EventoSeed(
        'Jazz en el sotano',
        'Trio de jazz en vivo con barra de tragos de autor.',
        'Thelonious Club', 'Salguero 1884, Palermo',
        -34.5889, -58.4105,
        1, time(22, 30), 2.5, ('bar', 'recital'), Decimal('6000'),
    ),
    EventoSeed(
        'Feria de diseno independiente',
        'Mas de 80 puestos de diseno, ilustracion y objetos.',
        'Plaza Serrano', 'Plaza Cortazar, Palermo Soho',
        -34.5885, -58.4300,
        2, time(11, 0), 8, ('feria', 'aire-libre'),
    ),
    EventoSeed(
        'Milonga de los domingos',
        'Clase abierta de tango y despues milonga hasta tarde.',
        'Plaza Dorrego', 'Humberto Primo y Defensa, San Telmo',
        -34.6206, -58.3714,
        3, time(19, 0), 5, ('aire-libre', 'taller'),
    ),
    EventoSeed(
        'Noche de los museos (avant premiere)',
        'Recorrido nocturno con guias por las salas principales.',
        'Museo Nacional de Bellas Artes', 'Av. del Libertador 1473',
        -34.5838, -58.3929,
        4, time(20, 0), 4, ('museo',),
    ),
    EventoSeed(
        'Clasico en la Bombonera',
        'Partido de primera division. Abrir puertas dos horas antes.',
        'Estadio Alberto J. Armando', 'Brandsen 805, La Boca',
        -34.6356, -58.3647,
        5, time(17, 0), 2, ('deportivo',), Decimal('25000'),
    ),
    EventoSeed(
        'Stand-up de medianoche',
        'Cuatro comediantes, show corto y bar abierto.',
        'Paseo La Plaza', 'Av. Corrientes 1660',
        -34.6043, -58.3893,
        1, time(23, 45), 1.5, ('teatro', 'bar'), Decimal('9000'),
    ),
    EventoSeed(
        'After de electronica',
        'DJ sets hasta el amanecer en una terraza frente al rio.',
        'Terrazas de Puerto Madero', 'Alicia Moreau de Justo 1100',
        -34.6110, -58.3632,
        6, time(1, 30), 5, ('recital', 'bar'), Decimal('12000'),
    ),
    EventoSeed(
        'Ciclo de cine clasico',
        'Proyeccion en 35 mm con presentacion de un critico.',
        'Sala Lugones', 'Av. Corrientes 1530',
        -34.6040, -58.3874,
        7, time(18, 0), 2.5, ('cine',), Decimal('3000'),
    ),
    EventoSeed(
        'Taller de ceramica para principiantes',
        'Torno y modelado a mano. Materiales incluidos.',
        'Taller Barro Vivo', 'Av. Cabildo 2100, Belgrano',
        -34.5617, -58.4563,
        8, time(10, 0), 3, ('taller',), Decimal('15000'),
    ),
    EventoSeed(
        'Mercado de sabores',
        'Food trucks, cerveza artesanal y musica en vivo.',
        'Parque Centenario', 'Av. Diaz Velez 4800, Caballito',
        -34.6066, -58.4357,
        9, time(12, 0), 9, ('gastronomia', 'aire-libre', 'feria'),
    ),
    EventoSeed(
        'Recorrido por el Rosedal',
        'Caminata guiada con fotografos aficionados.',
        'Rosedal de Palermo', 'Av. Infanta Isabel 410',
        -34.5718, -58.4174,
        10, time(8, 30), None, ('aire-libre',),
    ),
    EventoSeed(
        'Obra: La casa de Bernarda Alba',
        'Version contemporanea del clasico de Lorca.',
        'Teatro San Martin', 'Av. Corrientes 1530',
        -34.6041, -58.3870,
        12, time(20, 30), 2, ('teatro',), Decimal('11000'),
    ),
    EventoSeed(
        'Degustacion de vinos de altura',
        'Seis etiquetas del noroeste con maridaje.',
        'Vinoteca Recoleta', 'Ayacucho 1800, Recoleta',
        -34.5895, -58.3934,
        14, time(19, 30), 2, ('gastronomia', 'bar'), Decimal('18000'),
    ),
    EventoSeed(
        'Muestra de arte urbano',
        'Murales y obras de 20 artistas del street art local.',
        'Usina del Arte', 'Agustin R. Caffarena 1, La Boca',
        -34.6290, -58.3570,
        20, time(14, 0), 6, ('museo', 'otro'),
    ),
    EventoSeed(
        'Recital cancelado de prueba',
        'Evento cancelado: no deberia aparecer en la busqueda.',
        'Niceto Club', 'Cnel. Niceto Vega 5510, Palermo',
        -34.5868, -58.4377,
        3, time(21, 0), 3, ('recital',), Decimal('8000'),
        cancelado=True,
    ),
    # --- GBA ---
    EventoSeed(
        'Maraton nocturna',
        'Carrera de 10 km por el circuito del lago.',
        'Paseo del Bosque', 'Av. Iraola y 50, La Plata',
        -34.9108, -57.9365,
        11, time(21, 0), 2, ('deportivo', 'aire-libre'), Decimal('7000'),
    ),
    EventoSeed(
        'Feria artesanal del puerto',
        'Artesanias, plantas y comida casera junto al rio.',
        'Puerto de Frutos', 'Sarmiento 160, Tigre',
        -34.4180, -58.5810,
        2, time(10, 0), 8, ('feria',),
    ),
    # --- Otras ciudades ---
    EventoSeed(
        'Rock en el Monumento',
        'Bandas locales en el anfiteatro junto al Parana.',
        'Anfiteatro Humberto de Nito', 'Av. Belgrano y Rioja, Rosario',
        -32.9468, -60.6311,
        13, time(20, 0), 4, ('recital', 'aire-libre'), Decimal('5000'),
    ),
    EventoSeed(
        'Peña folklorica',
        'Empanadas, vino y chacarera hasta la madrugada.',
        'La Casona de Guemes', 'Belgrano 600, Cordoba',
        -31.4256, -64.1888,
        15, time(22, 0), 5, ('recital', 'gastronomia'), Decimal('4000'),
    ),
    EventoSeed(
        'Festival de cine de montana',
        'Documentales de escalada y charla con los directores.',
        'Teatro Independencia', 'Espejo 650, Mendoza',
        -32.8895, -68.8458,
        25, time(18, 30), 3, ('cine', 'aire-libre'),
    ),
    EventoSeed(
        'Taller de surf',
        'Clase introductoria con tabla y traje incluidos.',
        'Playa Grande', 'Paseo Jesus de Galindez, Mar del Plata',
        -38.0225, -57.5310,
        30, time(9, 0), 2, ('taller', 'deportivo', 'aire-libre'),
        Decimal('20000'),
    ),
    EventoSeed(
        'Encuentro de juegos de mesa',
        'Mesas libres y torneo de juegos de estrategia.',
        'Bar El Tablero', 'Calle 47 nro 500, La Plata',
        -34.9150, -57.9500,
        4, time(2, 0), 3, ('bar', 'otro'),
    ),
)
# fmt: on


def _instante(hoy: date, seed: EventoSeed, zona: ZoneInfo) -> datetime:
    local = datetime.combine(hoy + timedelta(days=seed.dias), seed.hora, zona)
    return local.astimezone(timezone.utc)


def construir_eventos(
    factory: EventoFactory,
    categorias: dict[str, Categoria],
    hoy: date,
    zona: ZoneInfo,
) -> list[Evento]:
    eventos = []
    for seed in EVENTOS:
        inicio = _instante(hoy, seed, zona)
        fin = (
            inicio + timedelta(hours=seed.duracion_horas)
            if seed.duracion_horas is not None
            else None
        )
        evento = factory.crear_seed(
            titulo=seed.titulo,
            descripcion=seed.descripcion,
            fecha_inicio=inicio,
            fecha_fin=fin,
            lugar=Lugar(
                nombre=seed.lugar,
                direccion=seed.direccion,
                latitud=seed.latitud,
                longitud=seed.longitud,
            ),
            categorias=[categorias[slug] for slug in seed.categorias],
            precio=seed.precio,
        )
        if seed.cancelado:
            evento.cancelar()
        eventos.append(evento)
    return eventos


async def _borrar_seed(session: AsyncSession) -> None:
    result = await session.execute(
        select(Evento).where(Evento.origen == OrigenEvento.SEED_EQUIPO)
    )
    for evento in result.scalars().all():
        await session.delete(evento)
        await session.delete(evento.lugar)
    await session.flush()


async def sembrar(
    session: AsyncSession,
    factory: EventoFactory,
    hoy: date,
    zona: ZoneInfo,
    reset: bool = False,
) -> int:
    """Devuelve cuantos eventos cargo: 0 si ya habia seed y no se pidio
    `reset`. No hace commit: lo decide quien la llama."""
    if reset:
        await _borrar_seed(session)
    else:
        existentes = await session.scalar(
            select(func.count())
            .select_from(Evento)
            .where(Evento.origen == OrigenEvento.SEED_EQUIPO)
        )
        if existentes:
            return 0

    slugs = sorted({slug for seed in EVENTOS for slug in seed.categorias})
    categorias = {
        c.slug: c
        for c in await SQLAlchemyCategoriaRepository(
            session
        ).get_activas_by_slugs(slugs)
    }
    faltantes = set(slugs) - categorias.keys()
    if faltantes:
        raise RuntimeError(
            'Faltan categorias en la base: '
            f'{", ".join(sorted(faltantes))}. '
            'Correr antes "alembic upgrade head".'
        )

    repo = SQLAlchemyEventoRepository(session)
    eventos = construir_eventos(factory, categorias, hoy, zona)
    for evento in eventos:
        await repo.add(evento)
    return len(eventos)


async def _main(reset: bool) -> None:
    # Import diferido: crea el engine con DATABASE_URL al importarse.
    from app.db.session import async_session_factory, engine  # noqa: PLC0415

    zona = ZoneInfo(get_settings().zona_horaria)
    hoy = datetime.now(zona).date()
    async with async_session_factory() as session:
        cargados = await sembrar(
            session, EventoFactory(zona), hoy, zona, reset=reset
        )
        await session.commit()
    await engine.dispose()

    if cargados:
        print(f'Se cargaron {cargados} eventos de seed.')
    else:
        print('Ya hay eventos de seed. Usar --reset para recargarlos.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        '--reset',
        action='store_true',
        help='Borra los eventos de seed existentes antes de cargar.',
    )
    asyncio.run(_main(parser.parse_args().reset))
