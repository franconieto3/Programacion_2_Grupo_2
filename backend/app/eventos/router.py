from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.auth.dependencies import get_usuario_actual
from app.eventos.dependencies import (
    get_buscar_eventos,
    get_cancelar_evento,
    get_editar_evento,
    get_listar_mis_eventos,
)
from app.eventos.schemas import (
    BusquedaEventosParams,
    EditarEventoRequest,
    EventoPublic,
    PaginaEventos,
)
from app.eventos.service import (
    BuscarEventos,
    CancelarEvento,
    EditarEvento,
    ListarMisEventos,
)
from app.models.usuario import Usuario
from app.organizadores.dependencies import require_organizador_aprobado
from app.organizadores.models import Organizador

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


# /mios tiene que declararse antes que GET /{id_evento}: si no, FastAPI
# interpreta "mios" como un id y responde 422.
@router.get(
    '/mios', response_model=list[EventoPublic], status_code=status.HTTP_200_OK
)
async def listar_mis_eventos(
    organizador: Organizador = Depends(require_organizador_aprobado),
    servicio: ListarMisEventos = Depends(get_listar_mis_eventos),
) -> list[EventoPublic]:
    """Eventos del organizador en cualquier estado, con su estado actual
    (RF-02.5)."""
    eventos = await servicio.ejecutar(organizador)
    return [EventoPublic.model_validate(e) for e in eventos]


@router.patch(
    '/{id_evento}', response_model=EventoPublic, status_code=status.HTTP_200_OK
)
async def editar_evento(
    id_evento: UUID,
    datos: EditarEventoRequest,
    organizador: Organizador = Depends(require_organizador_aprobado),
    servicio: EditarEvento = Depends(get_editar_evento),
) -> EventoPublic:
    """Solo el organizador duenio del evento (RF-02.4); si no, 403."""
    evento = await servicio.ejecutar(organizador, id_evento, datos)
    return EventoPublic.model_validate(evento)


@router.post(
    '/{id_evento}/cancelar',
    response_model=EventoPublic,
    status_code=status.HTTP_200_OK,
)
async def cancelar_evento(
    id_evento: UUID,
    organizador: Organizador = Depends(require_organizador_aprobado),
    servicio: CancelarEvento = Depends(get_cancelar_evento),
) -> EventoPublic:
    """Solo el organizador duenio del evento (RF-02.4); si no, 403."""
    evento = await servicio.ejecutar(organizador, id_evento)
    return EventoPublic.model_validate(evento)
