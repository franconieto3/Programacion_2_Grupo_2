"""Composition root del modulo de organizadores: el unico lugar que conoce
la implementacion concreta del repositorio. Los servicios solo ven el
Protocol OrganizadorRepository. Expone `require_organizador_aprobado` para
proteger los endpoints que crean o gestionan eventos (RF-01.7)."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_usuario_actual
from app.db.session import get_db_session
from app.models.usuario import Usuario
from app.organizadores.exceptions import OrganizadorNoAprobadoError
from app.organizadores.models import Organizador
from app.organizadores.repository import (
    OrganizadorRepository,
    SQLAlchemyOrganizadorRepository,
)
from app.organizadores.service import (
    AprobarOrganizador,
    ListarSolicitudesOrganizador,
    RechazarOrganizador,
    SolicitarOrganizador,
    SuspenderOrganizador,
)


def get_organizador_repository(
    session: AsyncSession = Depends(get_db_session),
) -> OrganizadorRepository:
    return SQLAlchemyOrganizadorRepository(session)


def get_solicitar_organizador(
    repo: OrganizadorRepository = Depends(get_organizador_repository),
) -> SolicitarOrganizador:
    return SolicitarOrganizador(repo)


def get_listar_solicitudes_organizador(
    repo: OrganizadorRepository = Depends(get_organizador_repository),
) -> ListarSolicitudesOrganizador:
    return ListarSolicitudesOrganizador(repo)


def get_aprobar_organizador(
    repo: OrganizadorRepository = Depends(get_organizador_repository),
) -> AprobarOrganizador:
    return AprobarOrganizador(repo)


def get_rechazar_organizador(
    repo: OrganizadorRepository = Depends(get_organizador_repository),
) -> RechazarOrganizador:
    return RechazarOrganizador(repo)


def get_suspender_organizador(
    repo: OrganizadorRepository = Depends(get_organizador_repository),
) -> SuspenderOrganizador:
    return SuspenderOrganizador(repo)


async def require_organizador_aprobado(
    usuario: Usuario = Depends(get_usuario_actual),
    repo: OrganizadorRepository = Depends(get_organizador_repository),
) -> Organizador:
    """Perfil de organizador del usuario autenticado, si puede publicar
    (RF-01.7). Se encadena sobre get_usuario_actual, asi que sin sesion
    valida responde 401 antes de llegar aca; sin perfil o con un perfil que
    no esta APROBADO, 403."""
    organizador = await repo.get_by_usuario_id(usuario.id)
    if organizador is None or not organizador.puede_publicar():
        raise OrganizadorNoAprobadoError()
    return organizador
