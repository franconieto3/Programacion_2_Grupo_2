import uuid
from datetime import datetime, timezone
from enum import StrEnum

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class EstadoOrganizador(StrEnum):
    PENDIENTE = 'PENDIENTE'
    APROBADO = 'APROBADO'
    RECHAZADO = 'RECHAZADO'
    SUSPENDIDO = 'SUSPENDIDO'


class Organizador(Base):
    """Perfil con el que un usuario publica eventos (CU-04). Composicion con
    Usuario, no herencia: el mismo usuario descubre y publica desde una sola
    cuenta, y el perfil tiene su propio ciclo de vida (estado).

    `id_usuario` es UNIQUE: garantiza la multiplicidad 0..1 del diagrama y
    es lo que impide dos solicitudes del mismo usuario aunque lleguen a la
    vez."""

    __tablename__ = 'organizadores'

    id_organizador: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    id_usuario: Mapped[uuid.UUID] = mapped_column(
        ForeignKey('usuario.id_usuario', ondelete='CASCADE'),
        unique=True,
        nullable=False,
    )
    nombre_publico: Mapped[str] = mapped_column(String(255), nullable=False)
    descripcion: Mapped[str] = mapped_column(Text, nullable=False)
    estado: Mapped[EstadoOrganizador] = mapped_column(
        Enum(EstadoOrganizador, name='estado_organizador'),
        default=EstadoOrganizador.PENDIENTE,
        nullable=False,
    )
    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    def puede_publicar(self) -> bool:
        return self.estado == EstadoOrganizador.APROBADO

    def reenviar_solicitud(
        self, nombre_publico: str, descripcion: str
    ) -> None:
        """Vuelve a PENDIENTE con los datos nuevos. Solo valido desde
        RECHAZADO (CU-04, flujo 5a); lo controla SolicitarOrganizador."""
        self.nombre_publico = nombre_publico
        self.descripcion = descripcion
        self.estado = EstadoOrganizador.PENDIENTE

    def aprobar(self) -> None:
        """Solo valido desde PENDIENTE (CU-05)."""
        from app.organizadores.exceptions import TransicionEstadoInvalidaError

        if self.estado != EstadoOrganizador.PENDIENTE:
            raise TransicionEstadoInvalidaError(
                self.estado, EstadoOrganizador.APROBADO
            )
        self.estado = EstadoOrganizador.APROBADO

    def rechazar(self) -> None:
        """Solo valido desde PENDIENTE (CU-05)."""
        from app.organizadores.exceptions import TransicionEstadoInvalidaError

        if self.estado != EstadoOrganizador.PENDIENTE:
            raise TransicionEstadoInvalidaError(
                self.estado, EstadoOrganizador.RECHAZADO
            )
        self.estado = EstadoOrganizador.RECHAZADO

    def suspender(self) -> None:
        """Solo valido desde APROBADO: para desactivar una PENDIENTE esta
        rechazar."""
        from app.organizadores.exceptions import TransicionEstadoInvalidaError

        if self.estado != EstadoOrganizador.APROBADO:
            raise TransicionEstadoInvalidaError(
                self.estado, EstadoOrganizador.SUSPENDIDO
            )
        self.estado = EstadoOrganizador.SUSPENDIDO
