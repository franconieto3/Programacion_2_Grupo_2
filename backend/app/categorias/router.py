from fastapi import APIRouter, Depends, status

from app.categorias.dependencies import get_listar_categorias
from app.categorias.schemas import CategoriaPublic
from app.categorias.service import ListarCategorias

router = APIRouter(prefix='/categorias', tags=['categorias'])


@router.get(
    '', response_model=list[CategoriaPublic], status_code=status.HTTP_200_OK
)
async def listar_categorias(
    servicio: ListarCategorias = Depends(get_listar_categorias),
) -> list[CategoriaPublic]:
    """Publico, sin token: el catalogo no tiene datos sensibles."""
    categorias = await servicio.ejecutar()
    return [CategoriaPublic.model_validate(c) for c in categorias]
