from sqlalchemy import Select

from app.eventos.schemas import BusquedaEventosParams


def filtrar_por_categorias(
    consulta: Select, filtros: BusquedaEventosParams
) -> Select:
    """Filtro por categorias (slugs) (RF-03.6).

    TODO (Persona D): por ahora no filtra.
    Un evento matchea si tiene al menos una de las categorias pedidas
    (tabla evento_categoria)."""
    return consulta
