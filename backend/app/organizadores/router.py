from fastapi import APIRouter, Depends, status
from app.organizadores.schemas import (
    SolicitudOrganizadorRequest, 
    OrganizadorPublic
)
from app.models.usuario import Usuario
from app.organizadores.service import SolicitarOrganizador
from app.organizadores.dependencies import get_solicitar_organizador
from app.auth.dependencies import get_usuario_actual

router = APIRouter(prefix="/organizadores", tags=["organizadores"])

@router.post("/solicitud", response_model = OrganizadorPublic, status_code = status.HTTP_201_CREATED)
async def solicitar_organizador(
    peticion: SolicitudOrganizadorRequest,
    usuario: Usuario = Depends(get_usuario_actual),
    servicio: SolicitarOrganizador = Depends(get_solicitar_organizador)
) -> OrganizadorPublic:
    
    resultado = await servicio.ejecutar(usuario, peticion)

    return OrganizadorPublic(
        id_organizador = resultado.id_organizador,
        id_usuario = resultado.id_usuario,
        nombre_publico = resultado.nombre_publico,
        descripcion = resultado.descripcion,
        estado = resultado.estado,
        fecha_creacion = resultado.fecha_creacion
    )