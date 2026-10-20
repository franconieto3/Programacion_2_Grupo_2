"""Puerto de persistencia de administradores (DIP): las dependencias solo
conocen AdministradorRepository (Protocol); SQLAlchemyAdministradorRepository
es la implementacion concreta y vive detras del composition root
(app/administradores/dependencies.py)."""

from typing import Protocol, runtime_checkable
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.administradores.models import Administrador


@runtime_checkable
class AdministradorRepository(Protocol):
    async def get_by_usuario_id(
        self, usuario_id: UUID
    ) -> Administrador | None: ...


class SQLAlchemyAdministradorRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_usuario_id(
        self, usuario_id: UUID
    ) -> Administrador | None:
        result = await self._session.execute(
            select(Administrador).where(Administrador.id_usuario == usuario_id)
        )
        return result.scalar_one_or_none()
