from datetime import date, datetime, time
from decimal import Decimal
from uuid import UUID

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)

from app.categorias.schemas import CategoriaPublic
from app.eventos.models import EstadoEvento, OrigenEvento


class BusquedaEventosParams(BaseModel):
    """Parametros de GET /eventos. Todos los filtros son opcionales; cada
    uno lo aplica su funcion en app/eventos/filtros/.

    - Viewport (RF-03.3): lat_min, lat_max, lng_min, lng_max. Vienen los
      cuatro o ninguno, y el minimo no puede superar al maximo (no se
      admiten viewports que crucen el antimeridiano); si no, 422.
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

    @model_validator(mode='after')
    def _viewport_completo_y_ordenado(self) -> 'BusquedaEventosParams':
        limites = (self.lat_min, self.lat_max, self.lng_min, self.lng_max)
        if all(limite is None for limite in limites):
            return self
        if any(limite is None for limite in limites):
            raise ValueError(
                'el viewport requiere lat_min, lat_max, lng_min y lng_max'
            )
        if self.lat_min > self.lat_max:
            raise ValueError('lat_min no puede ser mayor que lat_max')
        if self.lng_min > self.lng_max:
            raise ValueError('lng_min no puede ser mayor que lng_max')
        return self


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


class LugarRequest(BaseModel):
    """Ubicacion de un evento. Las coordenadas son obligatorias (RF-02.2)."""

    nombre: str | None = Field(default=None, max_length=255)
    direccion: str | None = Field(default=None, max_length=255)
    latitud: float = Field(ge=-90, le=90)
    longitud: float = Field(ge=-180, le=180)


class EditarEventoRequest(BaseModel):
    """Cuerpo de PATCH /eventos/{id_evento} (RF-02.4). Solo se modifican
    los campos enviados. `fecha_fin` y `precio` aceptan null para borrarlos;
    el resto, si se envia, no puede ser null. `lugar` reemplaza la ubicacion
    completa y `categorias` (slugs), la lista completa."""

    model_config = ConfigDict(extra='forbid')

    titulo: str | None = Field(default=None, min_length=1, max_length=255)
    descripcion: str | None = Field(default=None, min_length=1)
    fecha_inicio: AwareDatetime | None = None
    fecha_fin: AwareDatetime | None = None
    precio: Decimal | None = Field(
        default=None, ge=0, max_digits=10, decimal_places=2
    )
    lugar: LugarRequest | None = None
    categorias: list[str] | None = Field(default=None, min_length=1)

    @model_validator(mode='after')
    def _obligatorios_no_nulos(self) -> 'EditarEventoRequest':
        nulos = [
            campo
            for campo in (
                'titulo',
                'descripcion',
                'fecha_inicio',
                'lugar',
                'categorias',
            )
            if campo in self.model_fields_set and getattr(self, campo) is None
        ]
        if nulos:
            raise ValueError(f'No pueden ser null: {", ".join(nulos)}.')
        return self
