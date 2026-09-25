"""Implementacion concreta de AuditLogWriter (ver
app/auth/events/observers/audit_log_observer.py) sobre SQLAlchemy."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


class SQLAlchemyAuditLogWriter:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def record(self, *, event_type: str, email: str | None, detalle: str) -> None:
        self._session.add(AuditLog(event_type=event_type, email=email, detalle=detalle))
        await self._session.flush()
