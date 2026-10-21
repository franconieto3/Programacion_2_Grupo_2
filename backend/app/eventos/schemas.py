from datetime import date, datetime, time
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.categorias.schemas import CategoriaPublic
from app.eventos.models import EstadoEvento, OrigenEvento


class BusquedaEventosParams(BaseModel):
    """Parametros de GET /eventos. Todos los filtros son opcionales; cada
    uno lo aplica su funcion en app/eventos/filtros/.

    - Viewport (RF-03.3): lat_min, lat_max, lng_min, lng_max.
    - Fechas (RF-03.4): desde, hasta.
    - Horario (RF-03.5): hora_desde, hora_hasta, en formato HH:MM.
    - Categorias (RF-03.6): slugs, repitiendo el parametro
      (?categorias=bar&categorias=teatro)."""

    lat_min: float | None = Field(default=None, ge=-90, le=90)
    lat_max: float | None = Field(default=None, ge=-90, le=90)
    lng_min: float | None = Field(default=None, ge=-180, le=180)
    lng_max: float | None = Field(default=None, ge=-180, le=180)
    desde: date | None = None
    hasta: date | None = None
    hora_desde: time | None = None
    hora_hasta: time | None = None
    categorias: list[str] = Field(default_factory=list)
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class LugarPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_lugar: UUID
    nombre: str | None
    direccion: str | None
    latitud: float
    longitud: float


class EventoPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_evento: UUID
    id_organizador: UUID | None
    titulo: str
    descripcion: str
    fecha_inicio: datetime
    fecha_fin: datetime | None
    precio: Decimal | None
    estado: EstadoEvento
    origen: OrigenEvento
    lugar: LugarPublic
    categorias: list[CategoriaPublic]


class PaginaEventos(BaseModel):
    items: list[EventoPublic]
    total: int
    limit: int
    offset: int
