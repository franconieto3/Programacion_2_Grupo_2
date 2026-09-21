"""Servicio de tokens: JWT (access) + tokens opacos hasheados (refresh).

Este modulo vive en app/core/security (capa transversal) y no importa nada de
app/auth: define sus propios puertos angostos (RefreshTokenStore, UserLookup,
UserRecord) en vez de reutilizar UserRepository/RefreshTokenRepository de
app/auth/*.py. Esto evita un import circular (app.auth -> app.core.security ->
app.auth) y respeta ISP: al TokenService no le importa el resto de las
operaciones de esos repositorios (crear usuario, listar, etc.), solo estas.

Las implementaciones concretas de app/auth/repository.py y
app/auth/token_repository.py satisfacen estos Protocols estructuralmente, sin
heredar de ellos ni importarlos.
"""

from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Protocol, runtime_checkable
from uuid import UUID

from jose import ExpiredSignatureError, JWTError, jwt

from app.auth.exceptions import InvalidTokenError, TokenExpiredError


@runtime_checkable
class UserRecord(Protocol):
    """Vista minima de un usuario que necesita este servicio (ISP)."""

    id: UUID
    email: str
    rol: str
    activo: bool


@dataclass(frozen=True, slots=True)
class AccessTokenPayload:
    sub: UUID
    email: str
    rol: str
    exp: datetime


@dataclass(frozen=True, slots=True)
class RefreshTokenRecord:
    usuario_id: UUID
    expires_at: datetime
    revoked_at: datetime | None


@runtime_checkable
class RefreshTokenStore(Protocol):
    async def create(self, usuario_id: UUID, token_hash: str, expires_at: datetime) -> None: ...

    async def get_valid(self, token_hash: str) -> RefreshTokenRecord | None: ...

    async def revoke(self, token_hash: str) -> None: ...


@runtime_checkable
class UserLookup(Protocol):
    async def get_by_id(self, usuario_id: UUID) -> UserRecord | None: ...


@runtime_checkable
class TokenService(Protocol):
    def create_access_token(self, usuario: UserRecord) -> str: ...

    def decode_access_token(self, token: str) -> AccessTokenPayload: ...

    async def issue_refresh_token(self, usuario_id: UUID) -> str: ...

    async def resolve_refresh_token(self, raw_token: str) -> UserRecord: ...

    async def revoke_refresh_token(self, raw_token: str) -> None: ...


def _hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


class JoseTokenService:
    """Unica implementacion hoy: JWT (python-jose) para access tokens y
    tokens opacos hasheados (SHA-256) en base de datos para refresh tokens
    (nunca se persiste el token crudo, ver RNF-04)."""

    def __init__(
        self,
        *,
        secret_key: str,
        algorithm: str,
        access_token_ttl: timedelta,
        refresh_token_ttl: timedelta,
        refresh_store: RefreshTokenStore,
        user_lookup: UserLookup,
    ) -> None:
        self._secret_key = secret_key
        self._algorithm = algorithm
        self._access_token_ttl = access_token_ttl
        self._refresh_token_ttl = refresh_token_ttl
        self._refresh_store = refresh_store
        self._user_lookup = user_lookup

    def create_access_token(self, usuario: UserRecord) -> str:
        expires_at = datetime.now(timezone.utc) + self._access_token_ttl
        claims = {
            "sub": str(usuario.id),
            "email": usuario.email,
            "rol": usuario.rol,
            "exp": expires_at,
        }
        return jwt.encode(claims, self._secret_key, algorithm=self._algorithm)

    def decode_access_token(self, token: str) -> AccessTokenPayload:
        try:
            claims = jwt.decode(token, self._secret_key, algorithms=[self._algorithm])
        except ExpiredSignatureError as exc:
            raise TokenExpiredError() from exc
        except JWTError as exc:
            raise InvalidTokenError() from exc
        return AccessTokenPayload(
            sub=UUID(claims["sub"]),
            email=claims["email"],
            rol=claims["rol"],
            exp=datetime.fromtimestamp(claims["exp"], tz=timezone.utc),
        )

    async def issue_refresh_token(self, usuario_id: UUID) -> str:
        raw_token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + self._refresh_token_ttl
        await self._refresh_store.create(usuario_id, _hash_token(raw_token), expires_at)
        return raw_token

    async def resolve_refresh_token(self, raw_token: str) -> UserRecord:
        record = await self._refresh_store.get_valid(_hash_token(raw_token))
        if record is None or record.revoked_at is not None:
            raise InvalidTokenError()
        if record.expires_at < datetime.now(timezone.utc):
            raise TokenExpiredError()
        usuario = await self._user_lookup.get_by_id(record.usuario_id)
        if usuario is None or not usuario.activo:
            raise InvalidTokenError()
        return usuario

    async def revoke_refresh_token(self, raw_token: str) -> None:
        await self._refresh_store.revoke(_hash_token(raw_token))
