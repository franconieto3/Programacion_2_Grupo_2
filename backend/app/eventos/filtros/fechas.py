from sqlalchemy import Select

from app.eventos.schemas import BusquedaEventosParams


def filtrar_por_fechas(
    consulta: Select, filtros: BusquedaEventosParams
) -> Select:
    """Filtro por rango de fechas (desde, hasta) (RF-03.4).

    TODO (Persona D): por ahora no filtra.
    Ojo: fecha_inicio esta en UTC y desde/hasta son fechas locales
    (Settings.zona_horaria)."""
    return consulta
