from app.categorias.models import Categoria
from app.categorias.repository import CategoriaRepository


class ListarCategorias:
    """Catalogo de categorias activas (RF-04.1), para el alta de eventos
    (RF-02.3) y el filtro de busqueda (RF-03.6)."""

    def __init__(self, repo: CategoriaRepository) -> None:
        self._repo = repo

    async def ejecutar(self) -> list[Categoria]:
        return await self._repo.list_activas()
