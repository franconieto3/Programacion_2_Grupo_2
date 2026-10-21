"""Filtros de la busqueda de eventos (GET /eventos). Cada filtro es una
funcion `(consulta, filtros) -> consulta` en su propio archivo, para que
quien implementa uno no edite las mismas lineas que quien implementa otro.

Un filtro cuyo parametro no vino en la request devuelve la consulta sin
cambios. SQLAlchemyEventoRepository.buscar los aplica en orden sobre la
consulta de eventos visibles."""

from collections.abc import Callable

from sqlalchemy import Select

from app.eventos.filtros.categorias import filtrar_por_categorias
from app.eventos.filtros.fechas import filtrar_por_fechas
from app.eventos.filtros.horario import filtrar_por_horario
from app.eventos.filtros.viewport import filtrar_por_viewport
from app.eventos.schemas import BusquedaEventosParams

Filtro = Callable[[Select, BusquedaEventosParams], Select]

FILTROS: tuple[Filtro, ...] = (
    filtrar_por_viewport,
    filtrar_por_fechas,
    filtrar_por_horario,
    filtrar_por_categorias,
)
