"""Fixtures y dobles de test compartidos. Gracias a que Auth/las estrategias
solo dependen de Protocols (DIP), estos dobles no tocan SQLAlchemy, argon2 ni
python-jose: son simples estructuras en memoria."""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest

from app.auth.events.publisher import AuthEventPublisher
from app.auth.exceptions import InvalidTokenError, TokenExpiredError
from app.core.security.token_service import AccessTokenPayload
from app.models.usuario import RolEnum, Usuario


class InMemoryUserRepository:
    def __init__(self) -> None:
        self._by_id: dict[UUID, Usuario] = {}

    async def get_by_email(self, email: str) -> Usuario | None:
        return next((u for u in self._by_id.values() if u.email == email), None)

    async def get_by_id(self, usuario_id: UUID) -> Usuario | None:
        return self._by_id.get(usuario_id)

    async def create(
        self, *, email: str, password_hash: str, nombre: str, rol: RolEnum
    ) -> Usuario:
        usuario = Usuario(
            id=uuid4(),
            email=email,
            password_hash=password_hash,
            nombre=nombre,
            rol=rol,
            activo=True,
            creado_en=datetime.now(timezone.utc),
        )
        self._by_id[usuario.id] = usuario
        return usuario


class FakePasswordHasher:
    """Comparacion en texto plano con un prefijo, solo para tests. Nunca se
    usa en produccion: ahi va Argon2PasswordHasher (app/core/security/password_hasher.py)."""

    async def hash(self, plain_password: str) -> str:
        return f"hashed::{plain_password}"

    async def verify(self, plain_password: str, password_hash: str) -> bool:
        return password_hash == f"hashed::{plain_password}"


@dataclass
class _FakeRefreshRecord:
    usuario_id: UUID
    expires_at: datetime
    revoked_at: datetime | None = None


class FakeTokenService:
    """Implementa el Protocol TokenService en memoria (sin JWT real), para
    poder testear EmailSignIn/EmailVerify sin depender de python-jose."""

    def __init__(self) -> None:
        self._access_tokens: dict[str, AccessTokenPayload] = {}
        self._refresh_tokens: dict[str, _FakeRefreshRecord] = {}
        self._users_by_id: dict[UUID, Usuario] = {}
        self._counter = 0

    def register_user(self, usuario: Usuario) -> None:
        """Los tests usan esto para simular que el TokenService puede
        resolver un usuario a partir de su id (equivalente al UserLookup real
        respaldado por SQLAlchemy)."""
        self._users_by_id[usuario.id] = usuario

    def create_access_token(self, usuario: Usuario) -> str:
        self._counter += 1
        token = f"access-{self._counter}"
        self._access_tokens[token] = AccessTokenPayload(
            sub=usuario.id,
            email=usuario.email,
            rol=usuario.rol,
            exp=datetime.now(timezone.utc) + timedelta(minutes=15),
        )
        self._users_by_id[usuario.id] = usuario
        return token

    def decode_access_token(self, token: str) -> AccessTokenPayload:
        payload = self._access_tokens.get(token)
        if payload is None:
            raise InvalidTokenError()
        if payload.exp < datetime.now(timezone.utc):
            raise TokenExpiredError()
        return payload

    async def issue_refresh_token(self, usuario_id: UUID) -> str:
        self._counter += 1
        token = f"refresh-{self._counter}"
        self._refresh_tokens[token] = _FakeRefreshRecord(
            usuario_id=usuario_id, expires_at=datetime.now(timezone.utc) + timedelta(days=14)
        )
        return token

    async def resolve_refresh_token(self, raw_token: str) -> Usuario:
        record = self._refresh_tokens.get(raw_token)
        if record is None or record.revoked_at is not None:
            raise InvalidTokenError()
        if record.expires_at < datetime.now(timezone.utc):
            raise TokenExpiredError()
        usuario = self._users_by_id.get(record.usuario_id)
        if usuario is None:
            raise InvalidTokenError()
        return usuario

    async def revoke_refresh_token(self, raw_token: str) -> None:
        record = self._refresh_tokens.get(raw_token)
        if record is not None:
            record.revoked_at = datetime.now(timezone.utc)


class InMemoryResetTokenRepository:
    def __init__(self) -> None:
        self.created: list[tuple[UUID, str, datetime]] = []

    async def create(self, usuario_id: UUID, token_hash: str, expires_at: datetime) -> None:
        self.created.append((usuario_id, token_hash, expires_at))


@pytest.fixture
def user_repository() -> InMemoryUserRepository:
    return InMemoryUserRepository()


@pytest.fixture
def password_hasher() -> FakePasswordHasher:
    return FakePasswordHasher()


@pytest.fixture
def token_service() -> FakeTokenService:
    return FakeTokenService()


@pytest.fixture
def reset_token_repository() -> InMemoryResetTokenRepository:
    return InMemoryResetTokenRepository()


@pytest.fixture
def event_publisher() -> AuthEventPublisher:
    """Instancia fresca, NO el singleton global (AuthEventPublisher.get_instance()),
    para que los tests no compartan observers entre si."""
    return AuthEventPublisher()


@pytest.fixture(autouse=True)
def _reset_auth_event_publisher_singleton():
    yield
    AuthEventPublisher.reset_instance()
