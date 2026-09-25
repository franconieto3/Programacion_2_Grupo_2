"""Puertos de persistencia para refresh tokens y tokens de recuperacion de
contrasena. Las implementaciones concretas satisfacen estructuralmente los
Protocols angostos que declara app/core/security/token_service.py (DIP)."""

from datetime import datetime
from typing import Protocol, runtime_checkable
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security.token_service import RefreshTokenRecord
from app.models.password_reset_token import PasswordResetToken
from app.models.refresh_token import RefreshToken


class SQLAlchemyRefreshTokenRepository:
    """Satisface RefreshTokenStore (app/core/security/token_service.py) por
    estructura, sin heredar de el."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, usuario_id: UUID, token_hash: str, expires_at: datetime) -> None:
        self._session.add(
            RefreshToken(usuario_id=usuario_id, token_hash=token_hash, expires_at=expires_at)
        )
        await self._session.flush()

    async def get_valid(self, token_hash: str) -> RefreshTokenRecord | None:
        result = await self._session.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return RefreshTokenRecord(
            usuario_id=row.usuario_id, expires_at=row.expires_at, revoked_at=row.revoked_at
        )

    async def revoke(self, token_hash: str) -> None:
        await self._session.execute(
            update(RefreshToken)
            .where(RefreshToken.token_hash == token_hash, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=datetime.now())
        )
        await self._session.flush()


@runtime_checkable
class PasswordResetTokenRepository(Protocol):
    async def create(self, usuario_id: UUID, token_hash: str, expires_at: datetime) -> None: ...


class SQLAlchemyPasswordResetTokenRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, usuario_id: UUID, token_hash: str, expires_at: datetime) -> None:
        self._session.add(
            PasswordResetToken(usuario_id=usuario_id, token_hash=token_hash, expires_at=expires_at)
        )
        await self._session.flush()
