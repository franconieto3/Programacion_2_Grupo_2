from fastapi import APIRouter, Depends, status

from app.configuracion.dependencies import get_ubicacion_default
from app.configuracion.schemas import UbicacionDefaultPublic

router = APIRouter(prefix='/config', tags=['config'])


@router.get(
    '/ubicacion-default',
    response_model=UbicacionDefaultPublic,
    status_code=status.HTTP_200_OK,
)
async def obtener_ubicacion_default(
    ubicacion: UbicacionDefaultPublic = Depends(get_ubicacion_default),
) -> UbicacionDefaultPublic:
    """Donde se abre el mapa si el usuario rechaza el permiso de
    geolocalizacion (RF-03.8, flujo 3a de CU-01). Publico, sin token, como
    GET /categorias: no tiene datos sensibles y el frontend la necesita
    apenas carga."""
    return ubicacion
