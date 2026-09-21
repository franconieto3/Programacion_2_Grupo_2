import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AuditLog(Base):
    """Rastro de auditoria de seguridad (RNF-04), escrito por AuditLogObserver
    (ver app/auth/events/observers/audit_log_observer.py). No es un modelo de
    negocio del dominio de eventos, sino infraestructura de observabilidad de
    auth: por eso vive aca y no en docs/planning.md seccion 3."""

    __tablename__ = "audit_log"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    detalle: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    ocurrido_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
