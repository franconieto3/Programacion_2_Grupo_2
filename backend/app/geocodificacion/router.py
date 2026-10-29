from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.auth.dependencies import get_usuario_actual
from app.geocodificacion.dependencies import get_buscar_lugar
from app.geocodificacion.schemas import BusquedaLugarParams, LugarPublic
from app.geocodificacion.service import BuscarLugar
from app.models.usuario import Usuario

router = APIRouter(prefix='/geocodificacion', tags=['geocodificacion'])


@router.get(
    '/buscar',
    response_model=list[LugarPublic],
    status_code=status.HTTP_200_OK,
)
async def buscar_lugar(
    params: Annotated[BusquedaLugarParams, Query()],
    _usuario: Usuario = Depends(get_usuario_actual),
    servicio: BuscarLugar = Depends(get_buscar_lugar),
) -> list[LugarPublic]:
    """Requiere login, como GET /eventos: el actor de CU-02 es un usuario
    logueado, y asi la API no queda como un proxy anonimo de Nominatim
    (su politica prohibe el uso masivo, RNF-05.1). Sin coincidencias
    devuelve una lista vacia (flujo 2a de CU-02, lo resuelve el frontend);
    si Nominatim no responde, 503."""
    lugares = await servicio.ejecutar(params)
    return [LugarPublic.model_validate(lugar) for lugar in lugares]
