from sqlalchemy import Select

from app.eventos.models import Lugar
from app.eventos.schemas import BusquedaEventosParams


def filtrar_por_viewport(
    consulta: Select, filtros: BusquedaEventosParams
) -> Select:
    """Filtro por viewport (lat_min, lat_max, lng_min, lng_max) (RF-03.3).

    BusquedaEventosParams garantiza que vienen los cuatro limites o
    ninguno; sin viewport no filtra. Los bordes son inclusivos. La
    consulta ya hace join con Lugar."""
    if filtros.lat_min is None:
        return consulta
    return consulta.where(
        Lugar.latitud.between(filtros.lat_min, filtros.lat_max),
        Lugar.longitud.between(filtros.lng_min, filtros.lng_max),
    )
