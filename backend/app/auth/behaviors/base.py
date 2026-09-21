"""Las 4 interfaces `«interface»` del diagrama de clases (SignInBehavior,
RegisterBehavior, VerifyBehavior, RecoveryBehavior), en Python.

Se usan `typing.Protocol` (no `ABC`): son contratos puros sin estado ni logica
compartida, y `Protocol` permite que los decoradores (app/auth/decorators/*.py)
implementen la misma interfaz por estructura, sin encadenar herencia con la
estrategia concreta que envuelven (ver RateLimitedSignIn). `Credentials`, en
cambio, es `ABC` porque el diagrama la marca explicitamente como
`<<abstracta>>`, no como interfaz.
"""

from typing import Protocol, runtime_checkable

from app.auth.credentials import Credentials
from app.auth.results import AuthResult, RegisteredUser, SessionInfo


@runtime_checkable
class SignInBehavior(Protocol):
    async def sign_in(self, credentials: Credentials) -> AuthResult: ...


@runtime_checkable
class RegisterBehavior(Protocol):
    async def register(self, credentials: Credentials) -> RegisteredUser: ...


@runtime_checkable
class VerifyBehavior(Protocol):
    async def verify_session(self) -> SessionInfo: ...


@runtime_checkable
class RecoveryBehavior(Protocol):
    async def recover_password(self, credentials: Credentials) -> None: ...
