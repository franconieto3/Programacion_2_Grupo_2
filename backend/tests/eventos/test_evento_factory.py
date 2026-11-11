from datetime import datetime, time, timezone
from decimal import Decimal
from uuid import uuid4
from zoneinfo import ZoneInfo

from app.categorias.models import Categoria
from app.eventos.factory import EventoFactory
from app.eventos.models import EstadoEvento, Lugar, OrigenEvento
from app.organizadores.models import EstadoOrganizador, Organizador

AHORA = datetime(2026, 11, 20, 12, 0, tzinfo=timezone.utc)
BUENOS_AIRES = ZoneInfo('America/Argentina/Buenos_Aires')


def _factory() -> EventoFactory:
    return EventoFactory(BUENOS_AIRES, reloj=lambda: AHORA)


def test_crear_seed_fija_estado_origen_y_sin_organizador():
    bar = Categoria(slug='bar', nombre='Bar')
    lugar = Lugar(nombre='Plaza', latitud=-34.6, longitud=-58.4)

    evento = _factory().crear_seed(
        titulo='Recital',
        descripcion='Musica en vivo',
        fecha_inicio=datetime(2026, 11, 21, 0, 30, tzinfo=timezone.utc),
        fecha_fin=None,
        lugar=lugar,
        categorias=[bar],
        precio=Decimal('1500.00'),
    )

    assert evento.estado == EstadoEvento.PUBLICADO
    assert evento.origen == OrigenEvento.SEED_EQUIPO
    assert evento.id_organizador is None
    assert evento.fecha_publicacion == AHORA
    assert evento.lugar is lugar
    assert evento.categorias == [bar]
    assert evento.precio == Decimal('1500.00')


def test_crear_seed_programa_las_fechas_con_la_zona_configurada():
    inicio = datetime(2026, 11, 21, 0, 30, tzinfo=timezone.utc)
    fin = datetime(2026, 11, 21, 3, 0, tzinfo=timezone.utc)

    evento = _factory().crear_seed(
        titulo='Recital',
        descripcion='Musica en vivo',
        fecha_inicio=inicio,
        fecha_fin=fin,
        lugar=Lugar(latitud=-34.6, longitud=-58.4),
        categorias=[],
    )

    assert evento.fecha_inicio == inicio
    assert evento.fecha_fin == fin
    # 00:30 UTC son las 21:30 del dia anterior en Buenos Aires (UTC-3).
    assert evento.hora_inicio_local == time(21, 30)


def test_crear_desde_organizador_lo_publica_y_asocia_al_organizador():
    perfil = Organizador(
        id_organizador=uuid4(),
        id_usuario=uuid4(),
        nombre_publico='Bar Los Pinos',
        descripcion='Musica en vivo',
        estado=EstadoOrganizador.APROBADO,
    )
    bar = Categoria(slug='bar', nombre='Bar')
    lugar = Lugar(nombre='Plaza', latitud=-34.6, longitud=-58.4)

    evento = _factory().crear_desde_organizador(
        organizador=perfil,
        titulo='Recital',
        descripcion='Musica en vivo',
        fecha_inicio=datetime(2026, 11, 21, 0, 30, tzinfo=timezone.utc),
        fecha_fin=None,
        lugar=lugar,
        categorias=[bar],
    )

    assert evento.estado == EstadoEvento.PUBLICADO
    assert evento.origen == OrigenEvento.CARGA_ORGANIZADOR
    assert evento.id_organizador == perfil.id_organizador
    assert evento.fecha_publicacion == AHORA
    assert evento.lugar is lugar
    assert evento.categorias == [bar]
    assert evento.precio is None
    assert evento.hora_inicio_local == time(21, 30)
