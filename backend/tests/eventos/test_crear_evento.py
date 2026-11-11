"""Caso de uso CrearEvento (CU-03, RF-02.1 a RF-02.3), con repositorios en
memoria y una hora fija."""

from datetime import datetime, time, timedelta, timezone
from decimal import Decimal
from zoneinfo import ZoneInfo

import pytest
from pydantic import ValidationError

from app.eventos.exceptions import (
    CategoriasInvalidasError,
    FechaInicioPasadaError,
)
from app.eventos.factory import EventoFactory
from app.eventos.models import EstadoEvento, OrigenEvento
from app.eventos.schemas import CrearEventoRequest
from app.eventos.service import CrearEvento
from tests.eventos.test_gestion_eventos import (
    BAR,
    CINE,
    TEATRO,
    InMemoryCategoriaRepository,
    InMemoryEventoRepository,
    organizador,
)

AHORA = datetime(2026, 11, 20, 12, 0, tzinfo=timezone.utc)
BUENOS_AIRES = ZoneInfo('America/Argentina/Buenos_Aires')


@pytest.fixture
def repo() -> InMemoryEventoRepository:
    return InMemoryEventoRepository()


@pytest.fixture
def servicio(repo) -> CrearEvento:
    def reloj():
        return AHORA

    return CrearEvento(
        repo,
        InMemoryCategoriaRepository([BAR, TEATRO, CINE]),
        EventoFactory(BUENOS_AIRES, reloj=reloj),
        reloj=reloj,
    )


def _datos(**cambios) -> CrearEventoRequest:
    datos = {
        'titulo': 'Recital en la plaza',
        'descripcion': 'Musica en vivo',
        # 00:30 UTC del 21/11 son las 21:30 del 20/11 en Buenos Aires.
        'fecha_inicio': datetime(2026, 11, 21, 0, 30, tzinfo=timezone.utc),
        'lugar': {
            'nombre': 'Plaza Serrano',
            'direccion': 'Borges 1600',
            'latitud': -34.588,
            'longitud': -58.430,
        },
        'categorias': ['bar'],
    }
    datos.update(cambios)
    return CrearEventoRequest(**datos)


async def test_crea_el_evento_publicado_y_lo_guarda(servicio, repo):
    perfil = organizador()

    evento = await servicio.ejecutar(
        perfil,
        _datos(
            fecha_fin=datetime(2026, 11, 21, 3, 0, tzinfo=timezone.utc),
            precio=Decimal('1500.00'),
        ),
    )

    assert repo.eventos[evento.id_evento] is evento
    assert evento.estado == EstadoEvento.PUBLICADO
    assert evento.origen == OrigenEvento.CARGA_ORGANIZADOR
    assert evento.id_organizador == perfil.id_organizador
    assert evento.fecha_publicacion == AHORA
    assert evento.precio == Decimal('1500.00')
    assert evento.hora_inicio_local == time(21, 30)
    assert evento.fecha_fin == datetime(
        2026, 11, 21, 3, 0, tzinfo=timezone.utc
    )


async def test_crea_el_lugar_con_las_coordenadas(servicio):
    evento = await servicio.ejecutar(organizador(), _datos())

    assert evento.lugar.nombre == 'Plaza Serrano'
    assert evento.lugar.direccion == 'Borges 1600'
    assert evento.lugar.latitud == -34.588
    assert evento.lugar.longitud == -58.430


async def test_asocia_las_categorias_en_orden_y_sin_repetir(servicio):
    evento = await servicio.ejecutar(
        organizador(), _datos(categorias=['teatro', 'bar', 'teatro'])
    )

    assert [c.slug for c in evento.categorias] == ['teatro', 'bar']


@pytest.mark.parametrize(
    'categorias', [['inexistente'], ['cine'], ['bar', 'inexistente']]
)
async def test_categoria_inexistente_o_inactiva_lanza_error(
    servicio, repo, categorias
):
    with pytest.raises(CategoriasInvalidasError):
        await servicio.ejecutar(organizador(), _datos(categorias=categorias))

    assert repo.eventos == {}


@pytest.mark.parametrize(
    'inicio', [AHORA, AHORA - timedelta(minutes=1), AHORA - timedelta(days=3)]
)
async def test_fecha_de_inicio_no_futura_lanza_error(servicio, repo, inicio):
    with pytest.raises(FechaInicioPasadaError):
        await servicio.ejecutar(organizador(), _datos(fecha_inicio=inicio))

    assert repo.eventos == {}


# --- Validaciones del DTO (CU-03, flujo 8a) ---


@pytest.mark.parametrize(
    'fin',
    [
        datetime(2026, 11, 21, 0, 30, tzinfo=timezone.utc),
        datetime(2026, 11, 20, 23, 0, tzinfo=timezone.utc),
    ],
)
def test_fecha_fin_no_posterior_al_inicio_es_invalida(fin):
    with pytest.raises(ValueError, match='posterior'):
        _datos(fecha_fin=fin)


@pytest.mark.parametrize(
    'cambios',
    [
        {'titulo': ''},
        {'descripcion': ''},
        {'categorias': []},
        {'precio': Decimal('-1')},
        {'fecha_inicio': datetime(2026, 11, 21, 0, 30)},
        {'lugar': {'latitud': 91, 'longitud': -58.4}},
        {'lugar': {'latitud': -34.6, 'longitud': 181}},
        {'lugar': {'nombre': 'Sin coordenadas'}},
        {'campo_inventado': 'x'},
    ],
)
def test_datos_invalidos_son_rechazados(cambios):
    with pytest.raises(ValidationError):
        _datos(**cambios)
