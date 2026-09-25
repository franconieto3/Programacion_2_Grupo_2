"""Composition root del modulo de auth: el UNICO lugar que conoce las
implementaciones concretas (SQLAlchemy, argon2, jose). Auth y las estrategias
solo ven Protocols; FastAPI resuelve el arbol de dependencias por request via
`Depends`.

La familia de productos de cada proveedor (credenciales + 4 estrategias) se
crea a traves de un Abstract Factory (app/auth/factories.py): el router y
`get_auth` reciben la MISMA fabrica por request, asi que nunca se mezclan
credenciales de un proveedor con estrategias de otro.
"""

from datetime import timedelta

from fastapi import Cookie, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.auth import Auth
from app.auth.decorators.rate_limited_signin import InMemoryLoginAttemptsStore, RateLimitedSignIn
from app.auth.events.publisher import AuthEventPublisher
from app.auth.factories import AuthProviderFactory, EmailAuthFactory
from app.auth.repository import SQLAlchemyUserRepository, UserRepository
from app.auth.token_repository import (
    SQLAlchemyPasswordResetTokenRepository,
    SQLAlchemyRefreshTokenRepository,
)
from app.core.config import Settings, get_settings
from app.core.security.password_hasher import Argon2PasswordHasher, PasswordHasher
from app.core.security.token_service import JoseTokenService, TokenService
from app.db.session import get_db_session

# Instancias sin estado por proceso (no son el Singleton "de ejercicio", solo
# evitan reconstruir objetos triviales en cada request). El almacen de
# intentos de login SI tiene estado y debe sobrevivir entre requests para que
# el rate limiting funcione, por eso vive a nivel de modulo.
_password_hasher = Argon2PasswordHasher()
_login_attempts_store = InMemoryLoginAttemptsStore()


def get_password_hasher() -> PasswordHasher:
    return _password_hasher


def get_login_attempts_store() -> InMemoryLoginAttemptsStore:
    return _login_attempts_store


def get_auth_event_publisher() -> AuthEventPublisher:
    """El Singleton real: ver app/auth/events/publisher.py. Los observers se
    suscriben una unica vez en app/main.py (evento startup)."""
    return AuthEventPublisher.get_instance()


def get_user_repository(session: AsyncSession = Depends(get_db_session)) -> UserRepository:
    return SQLAlchemyUserRepository(session)


def get_token_service(
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> TokenService:
    refresh_store = SQLAlchemyRefreshTokenRepository(session)
    user_lookup = SQLAlchemyUserRepository(session)
    return JoseTokenService(
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        access_token_ttl=timedelta(minutes=settings.access_token_ttl_minutes),
        refresh_token_ttl=timedelta(days=settings.refresh_token_ttl_days),
        refresh_store=refresh_store,
        user_lookup=user_lookup,
    )


def get_reset_token_repository(
    session: AsyncSession = Depends(get_db_session),
) -> SQLAlchemyPasswordResetTokenRepository:
    return SQLAlchemyPasswordResetTokenRepository(session)


def get_auth_factory(
    user_repository: UserRepository = Depends(get_user_repository),
    password_hasher: PasswordHasher = Depends(get_password_hasher),
    token_service: TokenService = Depends(get_token_service),
    reset_token_repository: SQLAlchemyPasswordResetTokenRepository = Depends(
        get_reset_token_repository
    ),
    event_publisher: AuthEventPublisher = Depends(get_auth_event_publisher),
    settings: Settings = Depends(get_settings),
    authorization: str | None = Header(default=None),
    refresh_token: str | None = Cookie(default=None),
) -> AuthProviderFactory:
    """Resuelve la fabrica concreta (Abstract Factory) de la familia del
    proveedor de autenticacion. FastAPI cachea las dependencias por request,
    asi que el router y `get_auth` reciben la MISMA instancia.

    Punto de extension: hoy solo existe la familia Email. Para sumar OAuth se
    agrega un parametro que identifique al proveedor (ej. path/query
    `provider`) y se retorna `GoogleAuthFactory(...)` o
    `FacebookAuthFactory(...)` segun corresponda; ni Auth, ni el router, ni
    las estrategias existentes cambian (OCP).

    `verifySession()` no toma argumentos (fiel al diagrama): la sesion se
    extrae ACA y se le pasa a la fabrica, que la inyecta al construir la
    estrategia de verificacion."""
    access_token = None
    if authorization and authorization.lower().startswith("bearer "):
        access_token = authorization.split(" ", 1)[1].strip()
    return EmailAuthFactory(
        user_repository,
        password_hasher,
        token_service,
        reset_token_repository,
        event_publisher,
        reset_token_ttl=timedelta(minutes=settings.password_reset_token_ttl_minutes),
        access_token=access_token,
        refresh_token=refresh_token,
    )


def get_auth(
    factory: AuthProviderFactory = Depends(get_auth_factory),
    attempts_store: InMemoryLoginAttemptsStore = Depends(get_login_attempts_store),
    settings: Settings = Depends(get_settings),
) -> Auth:
    """Las 4 estrategias salen de la misma fabrica. El Decorator se ensambla
    aca, sobre el producto de la fabrica: `Auth` recibe el SignInBehavior ya
    envuelto en RateLimitedSignIn y no se entera (LSP + OCP), y cualquier
    proveedor futuro hereda el rate limiting sin hacer nada."""
    sign_in_behavior = RateLimitedSignIn(
        factory.create_sign_in_behavior(),
        attempts_store,
        max_attempts=settings.login_max_attempts,
        lockout_window=timedelta(minutes=settings.login_lockout_minutes),
    )
    return Auth(
        sign_in_behavior,
        factory.create_register_behavior(),
        factory.create_verify_behavior(),
        factory.create_recovery_behavior(),
    )
