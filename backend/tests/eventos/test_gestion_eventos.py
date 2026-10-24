"""Casos de uso de gestion de eventos: mis eventos (RF-02.5), editar y
cancelar (RF-02.4) y ocultar (RF-05.1), con repositorios en memoria."""

from datetime import datetime, time, timedelta, timezone
from decimal import Decimal
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

import pytest

from app.categorias.models import Categoria
from app.eventos.exceptions import (
    CategoriasInvalidasError,
    EventoNoEditableError,
    EventoNoEncontradoError,
    FechasEventoInvalidasError,
    NoEsDuenioDelEventoError,
    TransicionEstadoEventoInvalidaError,
)
from app.eventos.models import EstadoEvento, Evento, Lugar, OrigenEvento
from app.eventos.schemas import BusquedaEventosParams, EditarEventoRequest
from app.eventos.service import (
    CancelarEvento,
    EditarEvento,
    ListarMisEventos,
    OcultarEvento,
)
from app.organizadores.models import EstadoOrganizador, Organizador

BUENOS_AIRES = ZoneInfo('America/Argentina/Buenos_Aires')
INICIO = datetime(2026, 11, 21, 0, 30, tzinfo=timezone.utc)


class InMemoryEventoRepository:
    def __init__(self) -> None:
        self.eventos: dict[UUID, Evento] = {}

    async def buscar(
        self, filtros: BusquedaEventosParams, ahora: datetime
    ) -> tuple[list[Evento], int]:
        eventos = list(self.eventos.values())
        return eventos[filtros.offset : filtros.offset + filtros.limit], len(
            eventos
        )

    async def add(self, evento: Evento) -> Evento:
        self.eventos[evento.id_evento] = evento
        return evento

    async def get_by_id(self, id_evento: UUID) -> Evento | None:
        return self.eventos.get(id_evento)

    async def list_by_organizador(self, id_organizador: UUID) -> list[Evento]:
        return sorted(
            (
                e
                for e in self.eventos.values()
                if e.id_organizador == id_organizador
            ),
            key=lambda e: e.fecha_inicio,
            reverse=True,
        )


class InMemoryCategoriaRepository:
    def __init__(self, categorias: list[Categoria]) -> None:
        self._categorias = categorias

    async def list_activas(self) -> list[Categoria]:
        return [c for c in self._categorias if c.activa]

    async def get_activas_by_slugs(self, slugs: list[str]) -> list[Categoria]:
        return [c for c in self._categorias if c.activa and c.slug in slugs]


def organizador() -> Organizador:
    return Organizador(
        id_organizador=uuid4(),
        id_usuario=uuid4(),
        nombre_publico='Bar Los Pinos',
        descripcion='Musica en vivo',
        estado=EstadoOrganizador.APROBADO,
    )


def evento(
    duenio: Organizador | None,
    estado: EstadoEvento = EstadoEvento.PUBLICADO,
    inicio: datetime = INICIO,
    fin: datetime | None = None,
    titulo: str = 'Recital en la plaza',
) -> Evento:
    nuevo = Evento(
        id_evento=uuid4(),
        id_organizador=duenio.id_organizador if duenio else None,
        titulo=titulo,
        descripcion='Musica en vivo',
        precio=None,
        estado=estado,
        origen=(
            OrigenEvento.CARGA_ORGANIZADOR
            if duenio
            else OrigenEvento.SEED_EQUIPO
        ),
        lugar=Lugar(
            id_lugar=uuid4(), nombre='Plaza', latitud=-34.6, longitud=-58.4
        ),
        categorias=[Categoria(slug='recital', nombre='Recital')],
    )
    nuevo.programar(inicio, fin, BUENOS_AIRES)
    return nuevo


BAR = Categoria(slug='bar', nombre='Bar', activa=True)
TEATRO = Categoria(slug='teatro', nombre='Teatro', activa=True)
CINE = Categoria(slug='cine', nombre='Cine', activa=False)


@pytest.fixture
def repo() -> InMemoryEventoRepository:
    return InMemoryEventoRepository()


def _editar(repo) -> EditarEvento:
    return EditarEvento(
        repo, InMemoryCategoriaRepository([BAR, TEATRO, CINE]), BUENOS_AIRES
    )


# --- Mis eventos ---


async def test_mis_eventos_devuelve_solo_los_propios_en_cualquier_estado(repo):
    yo, otro = organizador(), organizador()
    propios = [
        await repo.add(evento(yo, estado=estado))
        for estado in (EstadoEvento.PUBLICADO, EstadoEvento.CANCELADO)
    ]
    await repo.add(evento(otro))
    await repo.add(evento(None))

    eventos = await ListarMisEventos(repo).ejecutar(yo)

    assert {e.id_evento for e in eventos} == {e.id_evento for e in propios}


# --- Editar ---


async def test_editar_cambia_solo_los_campos_enviados(repo):
    yo = organizador()
    original = await repo.add(evento(yo))

    editado = await _editar(repo).ejecutar(
        yo,
        original.id_evento,
        EditarEventoRequest(titulo='Nuevo titulo', precio=Decimal('2500')),
    )

    assert editado.titulo == 'Nuevo titulo'
    assert editado.precio == Decimal('2500')
    assert editado.descripcion == 'Musica en vivo'
    assert editado.fecha_inicio == INICIO


async def test_editar_fechas_recalcula_la_hora_local(repo):
    yo = organizador()
    original = await repo.add(evento(yo))
    nuevo_inicio = datetime(2026, 11, 22, 23, 0, tzinfo=timezone.utc)

    editado = await _editar(repo).ejecutar(
        yo,
        original.id_evento,
        EditarEventoRequest(fecha_inicio=nuevo_inicio),
    )

    assert editado.fecha_inicio == nuevo_inicio
    # 23:00 UTC son las 20:00 en Buenos Aires (UTC-3).
    assert editado.hora_inicio_local == time(20, 0)


async def test_editar_solo_fecha_fin_conserva_el_inicio(repo):
    yo = organizador()
    original = await repo.add(evento(yo))
    fin = INICIO + timedelta(hours=3)

    editado = await _editar(repo).ejecutar(
        yo, original.id_evento, EditarEventoRequest(fecha_fin=fin)
    )

    assert editado.fecha_inicio == INICIO
    assert editado.fecha_fin == fin


async def test_editar_permite_borrar_fecha_fin_y_precio(repo):
    yo = organizador()
    original = evento(yo, fin=INICIO + timedelta(hours=2))
    original.precio = Decimal('1000')
    await repo.add(original)

    editado = await _editar(repo).ejecutar(
        yo,
        original.id_evento,
        EditarEventoRequest.model_validate({
            'fecha_fin': None,
            'precio': None,
        }),
    )

    assert editado.fecha_fin is None
    assert editado.precio is None


async def test_editar_con_fin_anterior_al_inicio_falla(repo):
    yo = organizador()
    original = await repo.add(evento(yo))

    with pytest.raises(FechasEventoInvalidasError):
        await _editar(repo).ejecutar(
            yo,
            original.id_evento,
            EditarEventoRequest(fecha_fin=INICIO - timedelta(hours=1)),
        )


async def test_editar_reemplaza_categorias_y_lugar(repo):
    yo = organizador()
    original = await repo.add(evento(yo))

    editado = await _editar(repo).ejecutar(
        yo,
        original.id_evento,
        EditarEventoRequest.model_validate({
            'categorias': ['teatro', 'bar', 'teatro'],
            'lugar': {'nombre': 'Teatro', 'latitud': -31.4, 'longitud': -64.2},
        }),
    )

    assert [c.slug for c in editado.categorias] == ['teatro', 'bar']
    assert editado.lugar.nombre == 'Teatro'
    assert editado.lugar.direccion is None
    assert (editado.lugar.latitud, editado.lugar.longitud) == (-31.4, -64.2)


@pytest.mark.parametrize('slugs', [['bar', 'inexistente'], ['cine']])
async def test_editar_con_categorias_invalidas_falla(repo, slugs):
    yo = organizador()
    original = await repo.add(evento(yo))

    with pytest.raises(CategoriasInvalidasError) as exc:
        await _editar(repo).ejecutar(
            yo, original.id_evento, EditarEventoRequest(categorias=slugs)
        )

    assert exc.value.slugs == [s for s in slugs if s != 'bar']
    assert [c.slug for c in original.categorias] == ['recital']


async def test_editar_evento_ajeno_falla(repo):
    original = await repo.add(evento(organizador()))

    with pytest.raises(NoEsDuenioDelEventoError):
        await _editar(repo).ejecutar(
            organizador(), original.id_evento, EditarEventoRequest(titulo='x')
        )


async def test_editar_evento_de_seed_falla(repo):
    original = await repo.add(evento(None))

    with pytest.raises(NoEsDuenioDelEventoError):
        await _editar(repo).ejecutar(
            organizador(), original.id_evento, EditarEventoRequest(titulo='x')
        )


async def test_editar_evento_inexistente_falla(repo):
    with pytest.raises(EventoNoEncontradoError):
        await _editar(repo).ejecutar(
            organizador(), uuid4(), EditarEventoRequest(titulo='x')
        )


@pytest.mark.parametrize(
    'estado', [EstadoEvento.CANCELADO, EstadoEvento.OCULTO]
)
async def test_editar_evento_cancelado_u_oculto_falla(repo, estado):
    yo = organizador()
    original = await repo.add(evento(yo, estado=estado))

    with pytest.raises(EventoNoEditableError):
        await _editar(repo).ejecutar(
            yo, original.id_evento, EditarEventoRequest(titulo='x')
        )

    assert original.titulo == 'Recital en la plaza'


# --- Validaciones del DTO ---


@pytest.mark.parametrize(
    'datos',
    [
        {'titulo': None},
        {'fecha_inicio': None},
        {'categorias': []},
        {'precio': -1},
        {'fecha_inicio': '2026-11-21T20:00:00'},  # sin zona horaria
        {'lugar': {'latitud': 91, 'longitud': 0}},
        {'lugar': {'nombre': 'Sin coordenadas'}},
        {'estado': 'PUBLICADO'},  # no editable por esta via
    ],
)
def test_dto_de_edicion_rechaza_datos_invalidos(datos):
    with pytest.raises(ValueError):  # noqa: PT011
        EditarEventoRequest.model_validate(datos)


# --- Cancelar ---


async def test_cancelar_evento_propio(repo):
    yo = organizador()
    original = await repo.add(evento(yo))

    cancelado = await CancelarEvento(repo).ejecutar(yo, original.id_evento)

    assert cancelado.estado == EstadoEvento.CANCELADO


async def test_cancelar_evento_ajeno_falla(repo):
    original = await repo.add(evento(organizador()))

    with pytest.raises(NoEsDuenioDelEventoError):
        await CancelarEvento(repo).ejecutar(organizador(), original.id_evento)

    assert original.estado == EstadoEvento.PUBLICADO


async def test_cancelar_evento_ya_cancelado_falla(repo):
    yo = organizador()
    original = await repo.add(evento(yo, estado=EstadoEvento.CANCELADO))

    with pytest.raises(TransicionEstadoEventoInvalidaError):
        await CancelarEvento(repo).ejecutar(yo, original.id_evento)


# --- Ocultar ---


@pytest.mark.parametrize('duenio', [organizador(), None])
async def test_ocultar_cualquier_evento_publicado(repo, duenio):
    original = await repo.add(evento(duenio))

    oculto = await OcultarEvento(repo).ejecutar(original.id_evento)

    assert oculto.estado == EstadoEvento.OCULTO


async def test_ocultar_evento_inexistente_falla(repo):
    with pytest.raises(EventoNoEncontradoError):
        await OcultarEvento(repo).ejecutar(uuid4())


async def test_ocultar_evento_ya_oculto_falla(repo):
    original = await repo.add(evento(None, estado=EstadoEvento.OCULTO))

    with pytest.raises(TransicionEstadoEventoInvalidaError):
        await OcultarEvento(repo).ejecutar(original.id_evento)
