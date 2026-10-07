import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Usuario(Base):
    """Modelo de autenticacion. UUID como PK (RNF-04.3): no filtra volumen de
    usuarios ni permite enumeracion secuencial.

    Sin rol: todo usuario registrado puede descubrir eventos. La capacidad de
    publicarlos se obtiene aparte, como perfil de organizador aprobado.

    Los nombres de columna siguen el esquema acordado (id_usuario,
    fecha_creacion); los atributos Python conservan `id` y `creado_en`."""

    __tablename__ = "usuario"

    id: Mapped[uuid.UUID] = mapped_column(
        "id_usuario", primary_key=True, default=uuid.uuid4
    )
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    apellido: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    # Nullable: un usuario registrado via proveedor externo (login social)
    # no tiene contrasena local.
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    creado_en: Mapped[datetime] = mapped_column(
        "fecha_creacion",
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
