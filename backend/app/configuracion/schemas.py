from pydantic import BaseModel


class UbicacionDefaultPublic(BaseModel):
    """Mismos nombres que LugarPublic (app/geocodificacion/schemas.py): el
    frontend centra el mapa igual con una sugerencia del buscador que con la
    ubicacion por defecto. `zoom` es el nivel inicial del mapa, en la escala
    de los tiles de OSM (0 a 19)."""

    nombre: str
    lat: float
    lng: float
    zoom: int
