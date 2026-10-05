"""`Auth`, tal como la define el diagrama: contexto Strategy que agrega (no
hereda) las 4 estrategias por atributos privados y delega 1:1 en cada una.

No importa SQLAlchemy, argon2 ni jose: solo conoce los 4 Protocols de
app/auth/behaviors/base.py y Credentials. Todo lo concreto se resuelve en el
composition root (app/auth/dependencies.py).

Es generica en las credenciales de cada operacion, porque login, registro y
recuperacion transportan datos distintos (ver app/auth/credentials.py). Ej.:
`Auth[EmailCredentials, EmailRegistration, EmailRecoveryRequest]`."""

from app.auth.behaviors.base import (
    RecoveryBehavior,
    RegisterBehavior,
    SignInBehavior,
    VerifyBehavior,
)
from app.auth.credentials import Credentials
from app.auth.results import AuthResult, RegisteredUser, SessionInfo


class Auth[SignInC: Credentials, RegisterC: Credentials, RecoveryC: Credentials]:
    def __init__(
        self,
        sign_in_behavior: SignInBehavior[SignInC],
        register_behavior: RegisterBehavior[RegisterC],
        verify_behavior: VerifyBehavior,
        recovery_behavior: RecoveryBehavior[RecoveryC],
    ) -> None:
        self._sign_in_behavior = sign_in_behavior
        self._register_behavior = register_behavior
        self._verify_behavior = verify_behavior
        self._recovery_behavior = recovery_behavior

    async def sign_in(self, credentials: SignInC) -> AuthResult:
        return await self._sign_in_behavior.sign_in(credentials)

    async def register(self, credentials: RegisterC) -> RegisteredUser:
        return await self._register_behavior.register(credentials)

    async def verify_session(self) -> SessionInfo:
        return await self._verify_behavior.verify_session()

    async def recover_password(self, credentials: RecoveryC) -> None:
        await self._recovery_behavior.recover_password(credentials)
