import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RolEnum(str, enum.Enum):
    DEMANDANTE = "DEMANDANTE"
    OFERENTE = "OFERENTE"


class Usuario(Base):
    """Modelo de autenticacion. UUID como PK (RNF-04.3): no filtra volumen de
    usuarios ni permite enumeracion secuencial."""

    __tablename__ = "usuario"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    rol: Mapped[RolEnum] = mapped_column(Enum(RolEnum, native_enum=False), nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
