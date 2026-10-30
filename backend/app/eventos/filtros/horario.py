from sqlalchemy import Select, or_

from app.eventos.models import Evento
from app.eventos.schemas import BusquedaEventosParams


def filtrar_por_horario(
    consulta: Select, filtros: BusquedaEventosParams
) -> Select:
    """Filtro por rango horario (hora_desde, hora_hasta) (RF-03.5).

    Compara contra Evento.hora_inicio_local, que ya esta en hora local (es
    una columna indexable, RNF-01.2). Los extremos son inclusivos. Si
    `hora_desde` es posterior a `hora_hasta` el rango cruza la medianoche
    (22:00 a 02:00): coincide lo que empieza desde las 22:00 o hasta las
    02:00. Con un solo extremo, el otro queda abierto."""
    desde, hasta = filtros.hora_desde, filtros.hora_hasta
    hora = Evento.hora_inicio_local

    if desde is None and hasta is None:
        return consulta
    if hasta is None:
        return consulta.where(hora >= desde)
    if desde is None:
        return consulta.where(hora <= hasta)
    if desde <= hasta:
        return consulta.where(hora.between(desde, hasta))
    return consulta.where(or_(hora >= desde, hora <= hasta))
