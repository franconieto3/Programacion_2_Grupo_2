"""Observer concreto: persiste un rastro de auditoria de seguridad (RNF-04)
para los 5 eventos de auth. Unica responsabilidad: traducir el evento a una
fila de AuditLog."""

from typing import Protocol, runtime_checkable

from app.auth.events.auth_events import (
    AuthEvent,
    LoginFailed,
    LoginSucceeded,
    PasswordRecoveryRequested,
    SessionVerified,
    UserRegistered,
)


@runtime_checkable
class AuditLogWriter(Protocol):
    """Puerto angosto (ISP): a este observer solo le interesa poder escribir
    una fila, no el resto de las operaciones de un repositorio generico."""

    async def record(self, *, event_type: str, email: str | None, detalle: str) -> None: ...


class AuditLogObserver:
    def __init__(self, writer: AuditLogWriter) -> None:
        self._writer = writer

    async def handle(self, event: AuthEvent) -> None:
        event_type, email, detalle = _describe(event)
        await self._writer.record(event_type=event_type, email=email, detalle=detalle)


def _describe(event: AuthEvent) -> tuple[str, str | None, str]:
    if isinstance(event, UserRegistered):
        return "user_registered", event.email, f"usuario_id={event.usuario_id}"
    if isinstance(event, LoginSucceeded):
        return "login_succeeded", event.email, f"usuario_id={event.usuario_id}"
    if isinstance(event, LoginFailed):
        return "login_failed", event.email, f"reason={event.reason}"
    if isinstance(event, PasswordRecoveryRequested):
        exists = event.usuario_id is not None
        return "password_recovery_requested", event.email, f"cuenta_existente={exists}"
    if isinstance(event, SessionVerified):
        return "session_verified", event.email, f"via_refresh={event.via_refresh}"
    raise TypeError(f"Evento de auth no soportado: {event!r}")
