import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Administrador(Base):
    """Perfil que habilita a un usuario a gestionar la plataforma (por
    ejemplo, revisar las solicitudes de organizador del CU-04). Composicion
    con Usuario, igual que Organizador: Usuario sigue sin rol y la capacidad
    de administrar se obtiene teniendo una fila en esta tabla.

    `id_usuario` es UNIQUE: un usuario es administrador o no lo es
    (multiplicidad 0..1)."""

    __tablename__ = 'administradores'

    id_admin: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    id_usuario: Mapped[uuid.UUID] = mapped_column(
        ForeignKey('usuario.id_usuario', ondelete='CASCADE'),
        unique=True,
        nullable=False,
    )
    fecha_alta: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )
