from collections.abc import Callable
from datetime import datetime, timezone
from uuid import UUID
from zoneinfo import ZoneInfo

from app.categorias.models import Categoria
from app.categorias.repository import CategoriaRepository
from app.eventos.exceptions import (
    CategoriasInvalidasError,
    EventoNoEditableError,
    EventoNoEncontradoError,
    FechasEventoInvalidasError,
    NoEsDuenioDelEventoError,
)
from app.eventos.models import Evento
from app.eventos.repository import EventoRepository
from app.eventos.schemas import BusquedaEventosParams, EditarEventoRequest
from app.organizadores.models import Organizador


def _ahora_utc() -> datetime:
    return datetime.now(timezone.utc)


class BuscarEventos:
    """Busqueda de eventos visibles (RF-03): la comparten la vista mapa y la
    vista lista, asi que ambas muestran los mismos resultados (RF-03.2).

    `reloj` se inyecta para poder testear la regla de visibilidad con una
    hora fija."""

    def __init__(
        self,
        repo: EventoRepository,
        reloj: Callable[[], datetime] = _ahora_utc,
    ) -> None:
        self._repo = repo
        self._reloj = reloj

    async def ejecutar(
        self, filtros: BusquedaEventosParams
    ) -> tuple[list[Evento], int]:
        return await self._repo.buscar(filtros, self._reloj())


async def _obtener(repo: EventoRepository, id_evento: UUID) -> Evento:
    evento = await repo.get_by_id(id_evento)
    if evento is None:
        raise EventoNoEncontradoError()
    return evento


async def _obtener_propio(
    repo: EventoRepository, organizador: Organizador, id_evento: UUID
) -> Evento:
    """El evento, si pertenece al organizador. Uno de seed no tiene
    organizador, asi que tampoco es de nadie."""
    evento = await _obtener(repo, id_evento)
    if evento.id_organizador != organizador.id_organizador:
        raise NoEsDuenioDelEventoError()
    return evento


class ListarMisEventos:
    """ "Mis eventos" del organizador, en cualquier estado (RF-02.5)."""

    def __init__(self, repo: EventoRepository) -> None:
        self._repo = repo

    async def ejecutar(self, organizador: Organizador) -> list[Evento]:
        return await self._repo.list_by_organizador(organizador.id_organizador)


class EditarEvento:
    """Edicion parcial de un evento propio (RF-02.4). Las fechas se asignan
    con `programar()` para recalcular la hora local; las categorias se
    validan contra el catalogo activo."""

    def __init__(
        self,
        repo: EventoRepository,
        categorias: CategoriaRepository,
        zona: ZoneInfo,
    ) -> None:
        self._repo = repo
        self._categorias = categorias
        self._zona = zona

    async def ejecutar(
        self,
        organizador: Organizador,
        id_evento: UUID,
        datos: EditarEventoRequest,
    ) -> Evento:
        evento = await _obtener_propio(self._repo, organizador, id_evento)
        if not evento.es_editable():
            raise EventoNoEditableError(evento.estado)

        enviados = datos.model_fields_set
        if enviados & {'fecha_inicio', 'fecha_fin'}:
            self._reprogramar(evento, datos)
        if 'categorias' in enviados:
            evento.categorias = await self._categorias_activas(
                datos.categorias
            )
        if 'lugar' in enviados:
            evento.lugar.nombre = datos.lugar.nombre
            evento.lugar.direccion = datos.lugar.direccion
            evento.lugar.latitud = datos.lugar.latitud
            evento.lugar.longitud = datos.lugar.longitud
        for campo in ('titulo', 'descripcion', 'precio'):
            if campo in enviados:
                setattr(evento, campo, getattr(datos, campo))
        return evento

    def _reprogramar(self, evento: Evento, datos: EditarEventoRequest) -> None:
        """Combina las fechas enviadas con las actuales del evento: cambiar
        solo el inicio conserva el fin, y viceversa."""
        enviados = datos.model_fields_set
        inicio = (
            datos.fecha_inicio
            if 'fecha_inicio' in enviados
            else evento.fecha_inicio
        )
        fin = datos.fecha_fin if 'fecha_fin' in enviados else evento.fecha_fin
        if fin is not None and fin <= inicio:
            raise FechasEventoInvalidasError()
        evento.programar(inicio, fin, self._zona)

    async def _categorias_activas(self, slugs: list[str]) -> list[Categoria]:
        pedidos = list(dict.fromkeys(slugs))
        encontradas = await self._categorias.get_activas_by_slugs(pedidos)
        por_slug = {c.slug: c for c in encontradas}
        faltantes = [s for s in pedidos if s not in por_slug]
        if faltantes:
            raise CategoriasInvalidasError(faltantes)
        return [por_slug[s] for s in pedidos]


class CancelarEvento:
    """Baja de un evento propio por su organizador (RF-02.4)."""

    def __init__(self, repo: EventoRepository) -> None:
        self._repo = repo

    async def ejecutar(
        self, organizador: Organizador, id_evento: UUID
    ) -> Evento:
        evento = await _obtener_propio(self._repo, organizador, id_evento)
        evento.cancelar()
        return evento


class OcultarEvento:
    """Baja logica de cualquier evento por moderacion de un administrador
    (RF-05.1)."""

    def __init__(self, repo: EventoRepository) -> None:
        self._repo = repo

    async def ejecutar(self, id_evento: UUID) -> Evento:
        evento = await _obtener(self._repo, id_evento)
        evento.ocultar()
        return evento
