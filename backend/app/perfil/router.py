from fastapi import APIRouter, Depends

from app.administradores.dependencies import get_administrador_repository
from app.administradores.repository import AdministradorRepository
from app.auth.dependencies import get_usuario_actual
from app.models.usuario import Usuario
from app.organizadores.dependencies import get_organizador_repository
from app.organizadores.repository import OrganizadorRepository
from app.perfil.schemas import OrganizadorResumen, UsuarioActualResponse

router = APIRouter(prefix='/auth', tags=['auth'])


@router.get('/me', response_model=UsuarioActualResponse)
async def usuario_actual(
    usuario: Usuario = Depends(get_usuario_actual),
    organizadores: OrganizadorRepository = Depends(
        get_organizador_repository
    ),
    administradores: AdministradorRepository = Depends(
        get_administrador_repository
    ),
) -> UsuarioActualResponse:
    """Usuario autenticado con sus roles. El frontend lo pide despues del
    login y al restaurar la sesion, asi el usuario tiene siempre la misma
    forma. Solo acepta el access token (401 sin el, 403 si la cuenta esta
    inactiva, via get_usuario_actual)."""
    organizador = await organizadores.get_by_usuario_id(usuario.id)
    administrador = await administradores.get_by_usuario_id(usuario.id)
    return UsuarioActualResponse(
        id=usuario.id,
        email=usuario.email,
        nombre=usuario.nombre,
        apellido=usuario.apellido,
        organizador=(
            OrganizadorResumen.model_validate(organizador)
            if organizador is not None
            else None
        ),
        es_admin=administrador is not None,
    )
