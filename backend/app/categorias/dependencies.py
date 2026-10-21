"""Composition root del modulo de categorias: el unico lugar que conoce la
implementacion concreta del repositorio. Los servicios solo ven el Protocol
CategoriaRepository."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.categorias.repository import (
    CategoriaRepository,
    SQLAlchemyCategoriaRepository,
)
from app.categorias.service import ListarCategorias
from app.db.session import get_db_session


def get_categoria_repository(
    session: AsyncSession = Depends(get_db_session),
) -> CategoriaRepository:
    return SQLAlchemyCategoriaRepository(session)


def get_listar_categorias(
    repo: CategoriaRepository = Depends(get_categoria_repository),
) -> ListarCategorias:
    return ListarCategorias(repo)
