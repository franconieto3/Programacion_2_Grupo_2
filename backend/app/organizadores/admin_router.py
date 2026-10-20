"""Endpoints de administracion sobre organizadores. Separados de router.py
porque cuelgan de /admin y exigen perfil de administrador, pero reutilizan
la misma entidad y repositorio del modulo."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.administradores.dependencies import get_admin_actual
from app.models.usuario import Usuario
from app.organizadores.dependencies import (
    get_aprobar_organizador,
    get_listar_solicitudes_organizador,
    get_rechazar_organizador,
    get_suspender_organizador,
)
from app.organizadores.models import EstadoOrganizador, Organizador
from app.organizadores.schemas import OrganizadorPublic
from app.organizadores.service import (
    AprobarOrganizador,
    ListarSolicitudesOrganizador,
    RechazarOrganizador,
    SuspenderOrganizador,
)

router = APIRouter(prefix="/admin/organizadores", tags=["admin"])


def _a_publico(organizador: Organizador) -> OrganizadorPublic:
    return OrganizadorPublic(
        id_organizador=organizador.id_organizador,
        id_usuario=organizador.id_usuario,
        nombre_publico=organizador.nombre_publico,
        descripcion=organizador.descripcion,
        estado=organizador.estado,
        fecha_creacion=organizador.fecha_creacion,
    )


@router.get("", response_model = list[OrganizadorPublic], status_code = status.HTTP_200_OK)
async def listar_organizadores(
    estado: EstadoOrganizador = Query(...),
    _admin: Usuario = Depends(get_admin_actual),
    servicio: ListarSolicitudesOrganizador = Depends(get_listar_solicitudes_organizador)
) -> list[OrganizadorPublic]:

    resultado = await servicio.ejecutar(estado)

    return [_a_publico(organizador) for organizador in resultado]


@router.post(
    "/{id_organizador}/aprobar",
    response_model=OrganizadorPublic,
    status_code=status.HTTP_200_OK,
)
async def aprobar_organizador(
    id_organizador: UUID,
    _admin: Usuario = Depends(get_admin_actual),
    servicio: AprobarOrganizador = Depends(get_aprobar_organizador),
) -> OrganizadorPublic:
    return _a_publico(await servicio.ejecutar(id_organizador))


@router.post(
    "/{id_organizador}/rechazar",
    response_model=OrganizadorPublic,
    status_code=status.HTTP_200_OK,
)
async def rechazar_organizador(
    id_organizador: UUID,
    _admin: Usuario = Depends(get_admin_actual),
    servicio: RechazarOrganizador = Depends(get_rechazar_organizador),
) -> OrganizadorPublic:
    return _a_publico(await servicio.ejecutar(id_organizador))


@router.post(
    "/{id_organizador}/suspender",
    response_model=OrganizadorPublic,
    status_code=status.HTTP_200_OK,
)
async def suspender_organizador(
    id_organizador: UUID,
    _admin: Usuario = Depends(get_admin_actual),
    servicio: SuspenderOrganizador = Depends(get_suspender_organizador),
) -> OrganizadorPublic:
    return _a_publico(await servicio.ejecutar(id_organizador))
