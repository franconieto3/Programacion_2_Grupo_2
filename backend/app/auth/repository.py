"""Puerto de persistencia de usuarios (DIP): Auth y las estrategias solo
conocen UserRepository (Protocol); SQLAlchemyUserRepository es la unica
implementacion concreta y vive detras del composition root
(app/auth/dependencies.py)."""

from typing import Protocol, runtime_checkable
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.usuario import RolEnum, Usuario


@runtime_checkable
class UserRepository(Protocol):
    async def get_by_email(self, email: str) -> Usuario | None: ...

    async def get_by_id(self, usuario_id: UUID) -> Usuario | None: ...

    async def create(
        self, *, email: str, password_hash: str, nombre: str, rol: RolEnum
    ) -> Usuario: ...


class SQLAlchemyUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_email(self, email: str) -> Usuario | None:
        result = await self._session.execute(select(Usuario).where(Usuario.email == email))
        return result.scalar_one_or_none()

    async def get_by_id(self, usuario_id: UUID) -> Usuario | None:
        result = await self._session.execute(select(Usuario).where(Usuario.id == usuario_id))
        return result.scalar_one_or_none()

    async def create(
        self, *, email: str, password_hash: str, nombre: str, rol: RolEnum
    ) -> Usuario:
        usuario = Usuario(email=email, password_hash=password_hash, nombre=nombre, rol=rol)
        self._session.add(usuario)
        await self._session.flush()
        return usuario
