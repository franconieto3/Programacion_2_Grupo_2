from sqlalchemy import Select

from app.eventos.schemas import BusquedaEventosParams


def filtrar_por_horario(
    consulta: Select, filtros: BusquedaEventosParams
) -> Select:
    """Filtro por rango horario (hora_desde, hora_hasta) (RF-03.5).

    TODO (Persona D): por ahora no filtra.
    Comparar contra Evento.hora_inicio_local, que ya esta en hora local.
    Contemplar rangos que cruzan la medianoche (22:00 a 02:00)."""
    return consulta
