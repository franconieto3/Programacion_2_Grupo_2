from sqlalchemy import Select

from app.eventos.schemas import BusquedaEventosParams


def filtrar_por_viewport(
    consulta: Select, filtros: BusquedaEventosParams
) -> Select:
    """Filtro por viewport (lat_min, lat_max, lng_min, lng_max) (RF-03.3).

    TODO (Persona C): por ahora no filtra.
    La consulta ya hace join con Lugar, asi que se puede filtrar sobre
    Lugar.latitud y Lugar.longitud."""
    return consulta
