"""Composition root del modulo de auth: el UNICO lugar que conoce las
implementaciones concretas (SQLAlchemy, argon2, jose). Auth y las estrategias
solo ven Protocols; FastAPI resuelve el arbol de dependencias por request via
`Depends`.
"""

from datetime import timedelta

from fastapi import Cookie, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.auth import Auth
from app.auth.behaviors.email_recovery import EmailRecovery
from app.auth.behaviors.email_register import EmailRegister
from app.auth.behaviors.email_signin import EmailSignIn
from app.auth.behaviors.email_verify import EmailVerify
from app.auth.decorators.rate_limited_signin import InMemoryLoginAttemptsStore, RateLimitedSignIn
from app.auth.events.publisher import AuthEventPublisher
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


def get_register_behavior(
    user_repository: UserRepository = Depends(get_user_repository),
    password_hasher: PasswordHasher = Depends(get_password_hasher),
    event_publisher: AuthEventPublisher = Depends(get_auth_event_publisher),
) -> EmailRegister:
    return EmailRegister(user_repository, password_hasher, event_publisher)


def get_sign_in_behavior(
    user_repository: UserRepository = Depends(get_user_repository),
    password_hasher: PasswordHasher = Depends(get_password_hasher),
    token_service: TokenService = Depends(get_token_service),
    event_publisher: AuthEventPublisher = Depends(get_auth_event_publisher),
    attempts_store: InMemoryLoginAttemptsStore = Depends(get_login_attempts_store),
    settings: Settings = Depends(get_settings),
) -> RateLimitedSignIn:
    """El Decorator se ensambla aca: `Auth` recibe el SignInBehavior ya
    envuelto en RateLimitedSignIn y no se entera (LSP + OCP)."""
    base = EmailSignIn(user_repository, password_hasher, token_service, event_publisher)
    return RateLimitedSignIn(
        base,
        attempts_store,
        max_attempts=settings.login_max_attempts,
        lockout_window=timedelta(minutes=settings.login_lockout_minutes),
    )


def get_recovery_behavior(
    user_repository: UserRepository = Depends(get_user_repository),
    reset_token_repository: SQLAlchemyPasswordResetTokenRepository = Depends(
        get_reset_token_repository
    ),
    event_publisher: AuthEventPublisher = Depends(get_auth_event_publisher),
    settings: Settings = Depends(get_settings),
) -> EmailRecovery:
    return EmailRecovery(
        user_repository,
        reset_token_repository,
        event_publisher,
        reset_token_ttl=timedelta(minutes=settings.password_reset_token_ttl_minutes),
    )


def get_verify_behavior(
    token_service: TokenService = Depends(get_token_service),
    event_publisher: AuthEventPublisher = Depends(get_auth_event_publisher),
    authorization: str | None = Header(default=None),
    refresh_token: str | None = Cookie(default=None),
) -> EmailVerify:
    """`verifySession()` no toma argumentos (fiel al diagrama): la sesion se
    extrae ACA, al construir la estrategia, no dentro del metodo."""
    access_token = None
    if authorization and authorization.lower().startswith("bearer "):
        access_token = authorization.split(" ", 1)[1].strip()
    return EmailVerify(token_service, event_publisher, access_token, refresh_token)


def get_auth(
    sign_in_behavior: RateLimitedSignIn = Depends(get_sign_in_behavior),
    register_behavior: EmailRegister = Depends(get_register_behavior),
    verify_behavior: EmailVerify = Depends(get_verify_behavior),
    recovery_behavior: EmailRecovery = Depends(get_recovery_behavior),
) -> Auth:
    return Auth(sign_in_behavior, register_behavior, verify_behavior, recovery_behavior)
