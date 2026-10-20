"""Integracion de GET /admin/organizadores contra la app real de FastAPI, con
la persistencia reemplazada por dobles en memoria via
`app.dependency_overrides` (mismo enfoque que tests/auth/test_router_integration.py).
Se recorre la cadena completa de dependencias: get_usuario_actual (401) ->
get_admin_actual (403) -> caso de uso."""

from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.administradores.dependencies import get_administrador_repository
from app.administradores.models import Administrador
from app.auth.dependencies import get_token_service, get_user_repository
from app.main import app
from app.models.usuario import Usuario
from app.organizadores.dependencies import get_organizador_repository
from app.organizadores.models import EstadoOrganizador, Organizador
from tests.conftest import FakeTokenService, InMemoryUserRepository
from tests.organizadores.test_solicitar_organizador import (
    InMemoryOrganizadorRepository,
)


class InMemoryAdministradorRepository:
    def __init__(self) -> None:
        self._by_usuario_id: dict[UUID, Administrador] = {}

    def add(self, usuario_id: UUID) -> None:
        self._by_usuario_id[usuario_id] = Administrador(id_usuario=usuario_id)

    async def get_by_usuario_id(
        self, usuario_id: UUID
    ) -> Administrador | None:
        return self._by_usuario_id.get(usuario_id)


@pytest.fixture
def wired_app():
    user_repository = InMemoryUserRepository()
    token_service = FakeTokenService()
    admin_repo = InMemoryAdministradorRepository()
    organizador_repo = InMemoryOrganizadorRepository()

    app.dependency_overrides[get_user_repository] = lambda: user_repository
    app.dependency_overrides[get_token_service] = lambda: token_service
    app.dependency_overrides[get_administrador_repository] = lambda: admin_repo
    app.dependency_overrides[get_organizador_repository] = (
        lambda: organizador_repo
    )

    yield user_repository, token_service, admin_repo, organizador_repo

    app.dependency_overrides.clear()


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def _usuario_con_token(user_repository, token_service, email) -> tuple[Usuario, str]:
    usuario = await user_repository.create(
        email=email, password_hash="x", nombre="Ana", apellido="Gomez"
    )
    return usuario, token_service.create_access_token(usuario)


async def _perfil(organizador_repo, estado) -> Organizador:
    return await organizador_repo.add(
        Organizador(
            id_organizador=uuid4(),
            id_usuario=uuid4(),
            nombre_publico="Bar Los Pinos",
            descripcion="Musica en vivo",
            estado=estado,
        )
    )


async def test_sin_token_responde_401(wired_app):
    async with _client() as client:
        response = await client.get("/admin/organizadores?estado=PENDIENTE")
    assert response.status_code == 401


async def test_usuario_no_admin_responde_403(wired_app):
    user_repository, token_service, _, _ = wired_app
    _, token = await _usuario_con_token(user_repository, token_service, "a@a.com")

    async with _client() as client:
        response = await client.get(
            "/admin/organizadores?estado=PENDIENTE",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert response.status_code == 403


async def test_admin_lista_solo_las_pendientes(wired_app):
    user_repository, token_service, admin_repo, organizador_repo = wired_app
    usuario, token = await _usuario_con_token(user_repository, token_service, "admin@a.com")
    admin_repo.add(usuario.id)
    # En memoria no corre el default de la columna fecha_creacion.
    pendiente = await _perfil(organizador_repo, EstadoOrganizador.PENDIENTE)
    pendiente.fecha_creacion = usuario.creado_en
    await _perfil(organizador_repo, EstadoOrganizador.APROBADO)

    async with _client() as client:
        response = await client.get(
            "/admin/organizadores?estado=PENDIENTE",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["id_organizador"] == str(pendiente.id_organizador)
    assert body[0]["estado"] == "PENDIENTE"


async def test_estado_invalido_responde_422(wired_app):
    user_repository, token_service, admin_repo, _ = wired_app
    usuario, token = await _usuario_con_token(user_repository, token_service, "admin@a.com")
    admin_repo.add(usuario.id)

    async with _client() as client:
        response = await client.get(
            "/admin/organizadores?estado=INEXISTENTE",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert response.status_code == 422
