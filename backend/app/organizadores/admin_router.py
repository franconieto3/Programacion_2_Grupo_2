"""Endpoints de administracion sobre organizadores. Separados de router.py
porque cuelgan de /admin y exigen perfil de administrador, pero reutilizan
la misma entidad y repositorio del modulo."""

from fastapi import APIRouter, Depends, Query, status

from app.administradores.dependencies import get_admin_actual
from app.models.usuario import Usuario
from app.organizadores.dependencies import get_listar_solicitudes_organizador
from app.organizadores.models import EstadoOrganizador
from app.organizadores.schemas import OrganizadorPublic
from app.organizadores.service import ListarSolicitudesOrganizador

router = APIRouter(prefix="/admin/organizadores", tags=["admin"])


@router.get("", response_model = list[OrganizadorPublic], status_code = status.HTTP_200_OK)
async def listar_organizadores(
    estado: EstadoOrganizador = Query(...),
    _admin: Usuario = Depends(get_admin_actual),
    servicio: ListarSolicitudesOrganizador = Depends(get_listar_solicitudes_organizador)
) -> list[OrganizadorPublic]:

    resultado = await servicio.ejecutar(estado)

    return [
        OrganizadorPublic(
            id_organizador = organizador.id_organizador,
            id_usuario = organizador.id_usuario,
            nombre_publico = organizador.nombre_publico,
            descripcion = organizador.descripcion,
            estado = organizador.estado,
            fecha_creacion = organizador.fecha_creacion
        )
        for organizador in resultado
    ]
