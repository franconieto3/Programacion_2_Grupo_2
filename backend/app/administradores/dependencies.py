"""Composition root del modulo de administradores: el unico lugar que conoce
la implementacion concreta del repositorio. Expone `get_admin_actual` para
proteger los endpoints de administracion (/admin/...)."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.administradores.exceptions import NoEsAdministradorError
from app.administradores.repository import (
    AdministradorRepository,
    SQLAlchemyAdministradorRepository,
)
from app.auth.dependencies import get_usuario_actual
from app.db.session import get_db_session
from app.models.usuario import Usuario


def get_administrador_repository(
    session: AsyncSession = Depends(get_db_session),
) -> AdministradorRepository:
    return SQLAlchemyAdministradorRepository(session)


async def get_admin_actual(
    usuario: Usuario = Depends(get_usuario_actual),
    repo: AdministradorRepository = Depends(get_administrador_repository),
) -> Usuario:
    """Usuario autenticado que ademas es administrador. Se encadena sobre
    get_usuario_actual, asi que sin sesion valida responde 401 antes de
    llegar aca; con sesion pero sin perfil de administrador, 403."""
    if await repo.get_by_usuario_id(usuario.id) is None:
        raise NoEsAdministradorError()
    return usuario
