"""Composition root del modulo de configuracion. No hay repositorio ni
servicio: el dato sale de Settings y no tiene logica de negocio. Si algun
dia la ubicacion dependiera del usuario (ubicaciones guardadas, fase 2), ahi
aparece el caso de uso."""

from fastapi import Depends

from app.configuracion.schemas import UbicacionDefaultPublic
from app.core.config import Settings, get_settings


def get_ubicacion_default(
    settings: Settings = Depends(get_settings),
) -> UbicacionDefaultPublic:
    return UbicacionDefaultPublic(
        nombre=settings.ubicacion_default_nombre,
        lat=settings.ubicacion_default_lat,
        lng=settings.ubicacion_default_lng,
        zoom=settings.ubicacion_default_zoom,
    )
