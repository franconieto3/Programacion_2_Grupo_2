"""Puerto de persistencia de eventos (DIP): los servicios solo conocen
EventoRepository (Protocol); SQLAlchemyEventoRepository es la
implementacion concreta y vive detras del composition root
(app/eventos/dependencies.py)."""

from datetime import datetime
from typing import Protocol, runtime_checkable

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.eventos.filtros import FILTROS
from app.eventos.models import EstadoEvento, Evento
from app.eventos.schemas import BusquedaEventosParams


@runtime_checkable
class EventoRepository(Protocol):
    async def buscar(
        self, filtros: BusquedaEventosParams, ahora: datetime
    ) -> tuple[list[Evento], int]: ...


def solo_visibles(consulta: Select, ahora: datetime) -> Select:
    """Regla de visibilidad de la busqueda: solo eventos PUBLICADOS que no
    terminaron. Un evento con fecha_fin se muestra hasta que termina; uno
    sin fecha_fin, hasta que empieza."""
    return consulta.where(
        Evento.estado == EstadoEvento.PUBLICADO,
        func.coalesce(Evento.fecha_fin, Evento.fecha_inicio) >= ahora,
    )


class SQLAlchemyEventoRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def buscar(
        self, filtros: BusquedaEventosParams, ahora: datetime
    ) -> tuple[list[Evento], int]:
        """Devuelve la pagina pedida y el total de eventos que cumplen los
        filtros (para paginar). Orden: los mas proximos primero; el id
        desempata para que el orden sea estable entre paginas."""
        consulta = solo_visibles(select(Evento).join(Evento.lugar), ahora)
        for filtro in FILTROS:
            consulta = filtro(consulta, filtros)

        total = await self._session.scalar(
            select(func.count()).select_from(consulta.subquery())
        )
        result = await self._session.execute(
            consulta
            .order_by(Evento.fecha_inicio, Evento.id_evento)
            .limit(filtros.limit)
            .offset(filtros.offset)
        )
        return list(result.scalars().all()), total or 0
