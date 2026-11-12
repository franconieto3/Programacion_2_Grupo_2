"""Vencimiento del refresh token en JoseTokenService. SQLite devuelve las
fechas sin zona horaria (PostgreSQL con ella): las dos tienen que funcionar."""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest

from app.auth.exceptions import TokenExpiredError
from app.core.security.token_service import (
    JoseTokenService,
    RefreshTokenRecord,
)


@dataclass
class _Usuario:
    id: UUID
    email: str
    activo: bool = True


class _RefreshStore:
    """Devuelve siempre el registro con el vencimiento indicado."""

    def __init__(self, usuario_id: UUID, expires_at: datetime) -> None:
        self._record = RefreshTokenRecord(
            usuario_id=usuario_id, expires_at=expires_at, revoked_at=None
        )

    async def create(self, usuario_id, token_hash, expires_at) -> None: ...

    async def get_valid(self, token_hash: str) -> RefreshTokenRecord:
        return self._record

    async def revoke(self, token_hash: str) -> None: ...


class _UserLookup:
    def __init__(self, usuario: _Usuario) -> None:
        self._usuario = usuario

    async def get_by_id(self, usuario_id: UUID) -> _Usuario:
        return self._usuario


def _servicio(expires_at: datetime) -> tuple[JoseTokenService, _Usuario]:
    usuario = _Usuario(id=uuid4(), email='ana@example.com')
    servicio = JoseTokenService(
        secret_key='secreto-de-test',
        algorithm='HS256',
        access_token_ttl=timedelta(minutes=15),
        refresh_token_ttl=timedelta(days=7),
        refresh_store=_RefreshStore(usuario.id, expires_at),
        user_lookup=_UserLookup(usuario),
    )
    return servicio, usuario


def _ahora_utc_sin_zona() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


@pytest.mark.parametrize(
    'expires_at',
    [
        datetime.now(timezone.utc) + timedelta(days=1),
        _ahora_utc_sin_zona() + timedelta(days=1),
    ],
    ids=['con-zona-horaria', 'sin-zona-horaria'],
)
async def test_refresh_vigente_devuelve_el_usuario(expires_at):
    servicio, usuario = _servicio(expires_at)
    assert await servicio.resolve_refresh_token('token') is usuario


@pytest.mark.parametrize(
    'expires_at',
    [
        datetime.now(timezone.utc) - timedelta(minutes=1),
        _ahora_utc_sin_zona() - timedelta(minutes=1),
    ],
    ids=['con-zona-horaria', 'sin-zona-horaria'],
)
async def test_refresh_vencido_lanza_token_expirado(expires_at):
    servicio, _ = _servicio(expires_at)
    with pytest.raises(TokenExpiredError):
        await servicio.resolve_refresh_token('token')
