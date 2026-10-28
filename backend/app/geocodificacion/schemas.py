from pydantic import BaseModel, ConfigDict, Field


class BusquedaLugarParams(BaseModel):
    """Parametros de GET /geocodificacion/buscar. El minimo de 3
    caracteres evita mandarle a Nominatim busquedas que no sirven para nada
    (el frontend dispara la busqueda con debounce mientras se tipea)."""

    q: str = Field(min_length=3, max_length=200)
    limit: int = Field(default=5, ge=1, le=10)


class LugarPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    nombre: str
    tipo: str | None
    lat: float
    lng: float
    lat_min: float
    lat_max: float
    lng_min: float
    lng_max: float
