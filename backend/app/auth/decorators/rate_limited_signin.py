"""Decorator: agrega throttling por intentos fallidos a CUALQUIER
SignInBehavior, sin modificar EmailSignIn ni Auth (OCP). Implementa
SignInBehavior[C] por estructura (Protocol), envolviendo otro
SignInBehavior[C]; la clave de throttling es `credentials.identifier`, el unico
dato comun a todas las credenciales.

Mitigacion de fuerza bruta, RNF-04. Se descarto un `LoggingBehaviorDecorator`
generico adicional: AuditLogObserver ya cubre el registro estructurado de
eventos de auth (Observer), asi que un logging decorator duplicaria esa
responsabilidad sin resolver un problema nuevo.
"""

from datetime import datetime, timedelta, timezone
from typing import Protocol, runtime_checkable

from app.auth.behaviors.base import SignInBehavior
from app.auth.credentials import Credentials
from app.auth.exceptions import AccountTemporarilyLockedError, InvalidCredentialsError
from app.auth.results import AuthResult


@runtime_checkable
class LoginAttemptsStore(Protocol):
    async def is_locked(self, key: str, max_attempts: int, window: timedelta) -> bool: ...

    async def register_failure(self, key: str) -> None: ...

    async def reset(self, key: str) -> None: ...


class InMemoryLoginAttemptsStore:
    """Unica implementacion hoy. Limitacion conocida: no comparte estado
    entre workers si se corre `uvicorn --workers > 1` (aceptable para el TP,
    que corre un unico proceso; produccion real necesitaria Redis)."""

    def __init__(self) -> None:
        self._failures: dict[str, list[datetime]] = {}

    async def is_locked(self, key: str, max_attempts: int, window: timedelta) -> bool:
        self._purge_old(key, window)
        return len(self._failures.get(key, [])) >= max_attempts

    async def register_failure(self, key: str) -> None:
        self._failures.setdefault(key, []).append(datetime.now(timezone.utc))

    async def reset(self, key: str) -> None:
        self._failures.pop(key, None)

    def _purge_old(self, key: str, window: timedelta) -> None:
        cutoff = datetime.now(timezone.utc) - window
        attempts = self._failures.get(key)
        if attempts:
            self._failures[key] = [ts for ts in attempts if ts >= cutoff]


class RateLimitedSignIn[C: Credentials]:
    def __init__(
        self,
        wrapped: SignInBehavior[C],
        attempts_store: LoginAttemptsStore,
        max_attempts: int = 5,
        lockout_window: timedelta = timedelta(minutes=15),
    ) -> None:
        self._wrapped = wrapped
        self._attempts_store = attempts_store
        self._max_attempts = max_attempts
        self._lockout_window = lockout_window

    async def sign_in(self, credentials: C) -> AuthResult:
        key = credentials.identifier

        if await self._attempts_store.is_locked(key, self._max_attempts, self._lockout_window):
            raise AccountTemporarilyLockedError(key)

        try:
            result = await self._wrapped.sign_in(credentials)
        except InvalidCredentialsError:
            await self._attempts_store.register_failure(key)
            raise

        await self._attempts_store.reset(key)
        return result
