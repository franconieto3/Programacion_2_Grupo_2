"""Puerto de persistencia de categorias (DIP): los servicios solo conocen
CategoriaRepository (Protocol); SQLAlchemyCategoriaRepository es la
implementacion concreta y vive detras del composition root
(app/categorias/dependencies.py)."""

from typing import Protocol, runtime_checkable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.categorias.models import Categoria


@runtime_checkable
class CategoriaRepository(Protocol):
    async def list_activas(self) -> list[Categoria]: ...

    async def get_activas_by_slugs(
        self, slugs: list[str]
    ) -> list[Categoria]: ...


class SQLAlchemyCategoriaRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_activas(self) -> list[Categoria]:
        result = await self._session.execute(
            select(Categoria)
            .where(Categoria.activa.is_(True))
            .order_by(Categoria.nombre)
        )
        return list(result.scalars().all())

    async def get_activas_by_slugs(self, slugs: list[str]) -> list[Categoria]:
        """Devuelve solo las que existen y estan activas: quien la llama
        (por ejemplo, el alta de un evento) compara contra los slugs pedidos
        para detectar los invalidos."""
        if not slugs:
            return []
        result = await self._session.execute(
            select(Categoria).where(
                Categoria.slug.in_(slugs), Categoria.activa.is_(True)
            )
        )
        return list(result.scalars().all())
