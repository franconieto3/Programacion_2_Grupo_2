"""`Auth`, tal como la define el diagrama: contexto Strategy que agrega (no
hereda) las 4 estrategias por atributos privados y delega 1:1 en cada una.

No importa SQLAlchemy, argon2 ni jose: solo conoce los 4 Protocols de
app/auth/behaviors/base.py y Credentials. Todo lo concreto se resuelve en el
composition root (app/auth/dependencies.py)."""

from app.auth.behaviors.base import (
    RecoveryBehavior,
    RegisterBehavior,
    SignInBehavior,
    VerifyBehavior,
)
from app.auth.credentials import Credentials
from app.auth.results import AuthResult, RegisteredUser, SessionInfo


class Auth:
    def __init__(
        self,
        sign_in_behavior: SignInBehavior,
        register_behavior: RegisterBehavior,
        verify_behavior: VerifyBehavior,
        recovery_behavior: RecoveryBehavior,
    ) -> None:
        self._sign_in_behavior = sign_in_behavior
        self._register_behavior = register_behavior
        self._verify_behavior = verify_behavior
        self._recovery_behavior = recovery_behavior

    async def sign_in(self, credentials: Credentials) -> AuthResult:
        return await self._sign_in_behavior.sign_in(credentials)

    async def register(self, credentials: Credentials) -> RegisteredUser:
        return await self._register_behavior.register(credentials)

    async def verify_session(self) -> SessionInfo:
        return await self._verify_behavior.verify_session()

    async def recover_password(self, credentials: Credentials) -> None:
        await self._recovery_behavior.recover_password(credentials)
