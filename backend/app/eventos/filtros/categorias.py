from sqlalchemy import Select, select

from app.categorias.models import Categoria
from app.eventos.models import Evento, evento_categoria
from app.eventos.schemas import BusquedaEventosParams


def filtrar_por_categorias(
    consulta: Select, filtros: BusquedaEventosParams
) -> Select:
    """Filtro por categorias (slugs) (RF-03.6).

    Un evento coincide si tiene al menos una de las categorias pedidas.
    Se usa una subconsulta (`IN`) y no un join directo: con un join, un
    evento con dos categorias pedidas apareceria duplicado y se romperian
    el `total` y la paginacion. Un slug inexistente no coincide con nada.
    Sin categorias no filtra."""
    if not filtros.categorias:
        return consulta

    ids_de_eventos = (
        select(evento_categoria.c.id_evento)
        .join(
            Categoria,
            Categoria.id_categoria == evento_categoria.c.id_categoria,
        )
        .where(Categoria.slug.in_(filtros.categorias))
    )
    return consulta.where(Evento.id_evento.in_(ids_de_eventos))