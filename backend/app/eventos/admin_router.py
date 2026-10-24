"""Endpoints de moderacion de eventos. Separados de router.py porque
cuelgan de /admin y exigen perfil de administrador, igual que
app/organizadores/admin_router.py."""

from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.administradores.dependencies import get_admin_actual
from app.eventos.dependencies import get_ocultar_evento
from app.eventos.schemas import EventoPublic
from app.eventos.service import OcultarEvento
from app.models.usuario import Usuario

router = APIRouter(prefix='/admin/eventos', tags=['admin'])


@router.post(
    '/{id_evento}/ocultar',
    response_model=EventoPublic,
    status_code=status.HTTP_200_OK,
)
async def ocultar_evento(
    id_evento: UUID,
    _admin: Usuario = Depends(get_admin_actual),
    servicio: OcultarEvento = Depends(get_ocultar_evento),
) -> EventoPublic:
    """Baja logica por moderacion (RF-05.1): el evento deja de verse en la
    busqueda y en su detalle."""
    return EventoPublic.model_validate(await servicio.ejecutar(id_evento))
