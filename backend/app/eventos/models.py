import uuid
from datetime import datetime, time, timezone
from decimal import Decimal
from enum import StrEnum
from zoneinfo import ZoneInfo

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Numeric,
    String,
    Table,
    Text,
    Time,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.categorias.models import Categoria
from app.db.base import Base


class EstadoEvento(StrEnum):
    BORRADOR = 'BORRADOR'
    PUBLICADO = 'PUBLICADO'
    CANCELADO = 'CANCELADO'
    OCULTO = 'OCULTO'


class OrigenEvento(StrEnum):
    """Diferencia el contenido cargado por el equipo del publicado por
    organizadores reales (RF-05.2)."""

    CARGA_ORGANIZADOR = 'CARGA_ORGANIZADOR'
    SEED_EQUIPO = 'SEED_EQUIPO'


# Tabla intermedia de la asociacion N:M Evento - Categoria (RF-04.2). No es
# una clase porque no tiene datos propios.
evento_categoria = Table(
    'evento_categoria',
    Base.metadata,
    Column(
        'id_evento',
        Uuid,
        ForeignKey('eventos.id_evento', ondelete='CASCADE'),
        primary_key=True,
    ),
    Column(
        'id_categoria',
        ForeignKey('categoria_evento.id_categoria'),
        primary_key=True,
    ),
)


class Lugar(Base):
    """Donde ocurre un evento. Las coordenadas son el dato autoritativo
    (RF-02.2); nombre y direccion son descriptivos.

    Sin duenio: en el MVP cada alta de evento crea su lugar. Reutilizar
    lugares de eventos anteriores (RF-02.8) queda para fase 2."""

    __tablename__ = 'lugar'
    # Para el filtro por viewport (RF-03.3): un rango sobre latitud y otro
    # sobre longitud.
    __table_args__ = (
        Index('ix_lugar_latitud_longitud', 'latitud', 'longitud'),
    )

    id_lugar: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    nombre: Mapped[str | None] = mapped_column(String(255), nullable=True)
    direccion: Mapped[str | None] = mapped_column(String(255), nullable=True)
    latitud: Mapped[float] = mapped_column(Float, nullable=False)
    longitud: Mapped[float] = mapped_column(Float, nullable=False)


def hora_local(instante: datetime, zona: ZoneInfo) -> time:
    """Hora del dia de `instante` en `zona`, sin zona horaria."""
    return instante.astimezone(zona).time()


class Evento(Base):
    """Evento publicado en la plataforma.

    `fecha_inicio` y `fecha_fin` son timestamps con zona (se guardan en
    UTC). `hora_inicio_local` es un dato derivado de `fecha_inicio`: la hora
    del dia en la zona configurada (Settings.zona_horaria). Se guarda aparte
    para que el filtro horario (RF-03.5) sea una comparacion simple e
    indexable, sin convertir zonas dentro de la query. Para que nunca quede
    desincronizada, las fechas se asignan siempre con `programar()`.

    `id_organizador` es NULL en los eventos de seed (RF-05.2), que no
    pertenecen a ningun organizador."""

    __tablename__ = 'eventos'
    # Para la regla de visibilidad de la busqueda (estado + fecha).
    __table_args__ = (
        Index('ix_eventos_estado_fecha_inicio', 'estado', 'fecha_inicio'),
    )

    id_evento: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    id_organizador: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey('organizadores.id_organizador'),
        index=True,
        nullable=True,
    )
    id_lugar: Mapped[uuid.UUID] = mapped_column(
        ForeignKey('lugar.id_lugar'), index=True, nullable=False
    )
    titulo: Mapped[str] = mapped_column(String(255), nullable=False)
    descripcion: Mapped[str] = mapped_column(Text, nullable=False)
    fecha_inicio: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    fecha_fin: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    hora_inicio_local: Mapped[time] = mapped_column(Time, nullable=False)
    precio: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    estado: Mapped[EstadoEvento] = mapped_column(
        Enum(EstadoEvento, name='estado_evento'), nullable=False
    )
    origen: Mapped[OrigenEvento] = mapped_column(
        Enum(OrigenEvento, name='origen_evento'), nullable=False
    )
    # NULL mientras el evento es BORRADOR.
    fecha_publicacion: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    fecha_actualizacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    # selectin: la sesion es async y no admite lazy loading implicito, asi
    # que lugar y categorias se cargan junto con el evento.
    lugar: Mapped[Lugar] = relationship(lazy='selectin')
    categorias: Mapped[list[Categoria]] = relationship(
        secondary=evento_categoria, lazy='selectin'
    )

    def programar(
        self,
        fecha_inicio: datetime,
        fecha_fin: datetime | None,
        zona: ZoneInfo,
    ) -> None:
        """Asigna las fechas y recalcula `hora_inicio_local`. Las fechas
        deben venir con zona horaria."""
        self.fecha_inicio = fecha_inicio
        self.fecha_fin = fecha_fin
        self.hora_inicio_local = hora_local(fecha_inicio, zona)

    def es_editable(self) -> bool:
        """El organizador puede editar un evento BORRADOR o PUBLICADO
        (RF-02.4). Uno cancelado u oculto ya no se modifica."""
        return self.estado in {EstadoEvento.BORRADOR, EstadoEvento.PUBLICADO}

    def cancelar(self) -> None:
        """Lo decide el organizador (RF-02.4). Valido desde BORRADOR o
        PUBLICADO. Un evento cancelado deja de aparecer en la busqueda, pero
        sigue en "mis eventos" y en su detalle."""
        from app.eventos.exceptions import TransicionEstadoEventoInvalidaError

        if self.estado not in {EstadoEvento.BORRADOR, EstadoEvento.PUBLICADO}:
            raise TransicionEstadoEventoInvalidaError(
                self.estado, EstadoEvento.CANCELADO
            )
        self.estado = EstadoEvento.CANCELADO

    def ocultar(self) -> None:
        """Baja logica por moderacion de un administrador (RF-05.1). Valido
        desde PUBLICADO o CANCELADO: tambien permite bajar el detalle de un
        evento cancelado con contenido inapropiado."""
        from app.eventos.exceptions import TransicionEstadoEventoInvalidaError

        if self.estado not in {EstadoEvento.PUBLICADO, EstadoEvento.CANCELADO}:
            raise TransicionEstadoEventoInvalidaError(
                self.estado, EstadoEvento.OCULTO
            )
        self.estado = EstadoEvento.OCULTO
