from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.auth.dependencies import get_usuario_actual
from app.eventos.dependencies import get_buscar_eventos
from app.eventos.schemas import (
    BusquedaEventosParams,
    EventoPublic,
    PaginaEventos,
)
from app.eventos.service import BuscarEventos
from app.models.usuario import Usuario

router = APIRouter(prefix='/eventos', tags=['eventos'])


@router.get('', response_model=PaginaEventos, status_code=status.HTTP_200_OK)
async def buscar_eventos(
    filtros: Annotated[BusquedaEventosParams, Query()],
    _usuario: Usuario = Depends(get_usuario_actual),
    servicio: BuscarEventos = Depends(get_buscar_eventos),
) -> PaginaEventos:
    """Requiere login (RF-01.2). Devuelve solo eventos visibles: PUBLICADOS
    y que no terminaron."""
    eventos, total = await servicio.ejecutar(filtros)
    return PaginaEventos(
        items=[EventoPublic.model_validate(e) for e in eventos],
        total=total,
        limit=filtros.limit,
        offset=filtros.offset,
    )
