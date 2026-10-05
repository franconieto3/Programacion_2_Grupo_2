"""Las 4 interfaces `«interface»` del diagrama de clases (SignInBehavior,
RegisterBehavior, VerifyBehavior, RecoveryBehavior), en Python.

Se usan `typing.Protocol` (no `ABC`): son contratos puros sin estado ni logica
compartida, y `Protocol` permite que los decoradores (app/auth/decorators/*.py)
implementen la misma interfaz por estructura, sin encadenar herencia con la
estrategia concreta que envuelven (ver RateLimitedSignIn).

Las interfaces que reciben credenciales son genericas en `C`: cada estrategia
declara las credenciales concretas que acepta (ej. EmailSignIn cumple
`SignInBehavior[EmailCredentials]`), asi el type checker rechaza pasarle
credenciales de otro metodo de autenticacion. `C` solo aparece como parametro,
por lo que es contravariante: una estrategia que acepta cualquier
`Credentials` (ej. UnsupportedRecovery) sirve para cualquier `C`.
"""

from typing import Protocol, runtime_checkable

from app.auth.credentials import Credentials
from app.auth.results import AuthResult, RegisteredUser, SessionInfo


@runtime_checkable
class SignInBehavior[C: Credentials](Protocol):
    async def sign_in(self, credentials: C) -> AuthResult: ...


@runtime_checkable
class RegisterBehavior[C: Credentials](Protocol):
    async def register(self, credentials: C) -> RegisteredUser: ...


@runtime_checkable
class VerifyBehavior(Protocol):
    async def verify_session(self) -> SessionInfo: ...


@runtime_checkable
class RecoveryBehavior[C: Credentials](Protocol):
    async def recover_password(self, credentials: C) -> None: ...
