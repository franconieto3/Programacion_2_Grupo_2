"""Abstract Factory de proveedores de autenticacion.

Las credenciales y las 4 estrategias de un proveedor forman una FAMILIA de
productos relacionados: un `GoogleCredentials` solo tiene sentido junto a un
`GoogleSignIn`, nunca junto a un `EmailSignIn`. `AuthProviderFactory` unifica
la creacion de toda la familia en un unico objeto, de modo que el router
(credenciales) y `get_auth` (estrategias) reciben SIEMPRE la misma fabrica y
no pueden mezclar proveedores.

Familias proyectadas:
- Email:    EmailCredentials + EmailSignIn + EmailRegister + EmailVerify
            + EmailRecovery
- Google:   GoogleCredentials + GoogleSignIn + GoogleRegister + EmailVerify
            + UnsupportedRecovery
- Facebook: FacebookCredentials + FacebookSignIn + FacebookRegister + EmailVerify
            + UnsupportedRecovery

Hoy solo existe `EmailAuthFactory`. Agregar Google/Facebook es crear una
fabrica concreta nueva (y sus productos) y resolverla en
`app/auth/dependencies.py:get_auth_factory`, sin tocar Auth, el router ni las
estrategias existentes (OCP).
"""

from datetime import timedelta
from typing import Protocol, runtime_checkable

from app.auth.behaviors.base import (
    RecoveryBehavior,
    RegisterBehavior,
    SignInBehavior,
    VerifyBehavior,
)
from app.auth.behaviors.email_recovery import EmailRecovery
from app.auth.behaviors.email_register import EmailRegister
from app.auth.behaviors.email_signin import EmailSignIn
from app.auth.behaviors.email_verify import EmailVerify
from app.auth.credentials import Credentials
from app.auth.credentials_factory import CredentialsFactory, Peticion
from app.auth.events.publisher import AuthEventPublisher
from app.auth.repository import UserRepository
from app.auth.token_repository import PasswordResetTokenRepository
from app.core.security.password_hasher import PasswordHasher
from app.core.security.token_service import TokenService


@runtime_checkable
class AuthProviderFactory(Protocol):
    """Abstract Factory: declara la creacion de cada producto de la familia
    de un proveedor de autenticacion."""

    def create_credentials(self, peticion: Peticion) -> Credentials: ...

    def create_sign_in_behavior(self) -> SignInBehavior: ...

    def create_register_behavior(self) -> RegisterBehavior: ...

    def create_verify_behavior(self) -> VerifyBehavior: ...

    def create_recovery_behavior(self) -> RecoveryBehavior: ...


class EmailAuthFactory:
    """Fabrica concreta de la familia Email (email + contrasena local).

    Recibe por constructor todas las dependencias de la familia: el
    composition root (app/auth/dependencies.py) es quien conoce las
    implementaciones concretas (SQLAlchemy, argon2, jose) y se las inyecta.
    """

    def __init__(
        self,
        user_repository: UserRepository,
        password_hasher: PasswordHasher,
        token_service: TokenService,
        reset_token_repository: PasswordResetTokenRepository,
        event_publisher: AuthEventPublisher,
        reset_token_ttl: timedelta,
        access_token: str | None = None,
        refresh_token: str | None = None,
    ) -> None:
        self._user_repository = user_repository
        self._password_hasher = password_hasher
        self._token_service = token_service
        self._reset_token_repository = reset_token_repository
        self._event_publisher = event_publisher
        self._reset_token_ttl = reset_token_ttl
        self._access_token = access_token
        self._refresh_token = refresh_token

    def create_credentials(self, peticion: Peticion) -> Credentials:
        # La traduccion DTO -> EmailCredentials ya vive en el Simple Factory
        # original; se reutiliza en vez de duplicarla.
        return CredentialsFactory.create_credentials(peticion)

    def create_sign_in_behavior(self) -> SignInBehavior:
        return EmailSignIn(
            self._user_repository, self._password_hasher, self._token_service, self._event_publisher
        )

    def create_register_behavior(self) -> RegisterBehavior:
        return EmailRegister(self._user_repository, self._password_hasher, self._event_publisher)

    def create_verify_behavior(self) -> VerifyBehavior:
        return EmailVerify(
            self._token_service, self._event_publisher, self._access_token, self._refresh_token
        )

    def create_recovery_behavior(self) -> RecoveryBehavior:
        return EmailRecovery(
            self._user_repository,
            self._reset_token_repository,
            self._event_publisher,
            reset_token_ttl=self._reset_token_ttl,
        )
