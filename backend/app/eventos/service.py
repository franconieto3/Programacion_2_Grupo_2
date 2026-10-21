from collections.abc import Callable
from datetime import datetime, timezone

from app.eventos.models import Evento
from app.eventos.repository import EventoRepository
from app.eventos.schemas import BusquedaEventosParams


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
