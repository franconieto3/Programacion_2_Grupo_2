"""Eventos de dominio publicados por las estrategias de auth (Observer). Cada
uno es inmutable y lleva solo los datos que un observer podria necesitar."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True, slots=True)
class UserRegistered:
    usuario_id: UUID
    email: str
    nombre: str
    occurred_at: datetime = field(default_factory=_now)


@dataclass(frozen=True, slots=True)
class LoginSucceeded:
    usuario_id: UUID
    email: str
    occurred_at: datetime = field(default_factory=_now)


@dataclass(frozen=True, slots=True)
class LoginFailed:
    email: str
    reason: str
    occurred_at: datetime = field(default_factory=_now)


@dataclass(frozen=True, slots=True)
class PasswordRecoveryRequested:
    email: str
    usuario_id: UUID | None
    """None si el email no correspondia a ninguna cuenta (ver mitigacion de
    enumeracion de usuarios: el endpoint publica igual el evento, pero sin
    token, para que el tiempo de respuesta no delate la diferencia)."""
    reset_token: str | None
    occurred_at: datetime = field(default_factory=_now)


@dataclass(frozen=True, slots=True)
class SessionVerified:
    usuario_id: UUID
    email: str
    via_refresh: bool
    occurred_at: datetime = field(default_factory=_now)


AuthEvent = (
    UserRegistered | LoginSucceeded | LoginFailed | PasswordRecoveryRequested | SessionVerified
)
