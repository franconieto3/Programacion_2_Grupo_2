"""Factory de eventos: el unico lugar que arma un Evento nuevo. Cada origen
(seed del equipo, carga de un organizador) tiene su metodo, que fija estado,
origen y duenio de forma consistente, y asigna las fechas siempre con
`Evento.programar()` para que `hora_inicio_local` no quede desincronizada."""

from collections.abc import Callable
from datetime import datetime, timezone
from decimal import Decimal
from zoneinfo import ZoneInfo

from app.categorias.models import Categoria
from app.eventos.models import EstadoEvento, Evento, Lugar, OrigenEvento


def _ahora_utc() -> datetime:
    return datetime.now(timezone.utc)


class EventoFactory:
    """`zona` es Settings.zona_horaria; `reloj` se inyecta para poder
    testear `fecha_publicacion` con una hora fija."""

    def __init__(
        self,
        zona: ZoneInfo,
        reloj: Callable[[], datetime] = _ahora_utc,
    ) -> None:
        self._zona = zona
        self._reloj = reloj

    def crear_seed(  # noqa: PLR0913, PLR0917
        self,
        titulo: str,
        descripcion: str,
        fecha_inicio: datetime,
        fecha_fin: datetime | None,
        lugar: Lugar,
        categorias: list[Categoria],
        precio: Decimal | None = None,
    ) -> Evento:
        """Evento cargado por el equipo (RF-05.2): sin organizador y ya
        PUBLICADO, para que aparezca en la busqueda."""
        evento = Evento(
            titulo=titulo,
            descripcion=descripcion,
            precio=precio,
            estado=EstadoEvento.PUBLICADO,
            origen=OrigenEvento.SEED_EQUIPO,
            id_organizador=None,
            fecha_publicacion=self._reloj(),
            lugar=lugar,
            categorias=categorias,
        )
        evento.programar(fecha_inicio, fecha_fin, self._zona)
        return evento
