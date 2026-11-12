"""Integracion de GET /auth/me contra la app real de FastAPI, con la
persistencia reemplazada por dobles en memoria via `app.dependency_overrides`
(mismo enfoque que tests/organizadores/test_admin_router_integration.py)."""

from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.administradores.dependencies import get_administrador_repository
from app.auth.dependencies import get_token_service, get_user_repository
from app.main import app
from app.organizadores.dependencies import get_organizador_repository
from app.organizadores.models import EstadoOrganizador, Organizador
from tests.conftest import (
    FakeTokenService,
    InMemoryAdministradorRepository,
    InMemoryUserRepository,
)
from tests.organizadores.test_solicitar_organizador import (
    InMemoryOrganizadorRepository,
)


class Entorno:
    def __init__(self) -> None:
        self.usuarios = InMemoryUserRepository()
        self.tokens = FakeTokenService()
        self.admins = InMemoryAdministradorRepository()
        self.organizadores = InMemoryOrganizadorRepository()

    async def usuario_con_token(self, email='a@a.com'):
        usuario = await self.usuarios.create(
            email=email, password_hash='x', nombre='Ana', apellido='Gomez'
        )
        return usuario, self.tokens.create_access_token(usuario)


@pytest.fixture
def entorno():
    e = Entorno()
    app.dependency_overrides[get_user_repository] = lambda: e.usuarios
    app.dependency_overrides[get_token_service] = lambda: e.tokens
    app.dependency_overrides[get_administrador_repository] = lambda: e.admins
    app.dependency_overrides[get_organizador_repository] = (
        lambda: e.organizadores
    )
    yield e
    app.dependency_overrides.clear()


async def _get_me(token: str | None = None):
    headers = {'Authorization': f'Bearer {token}'} if token else {}
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url='http://test'
    ) as client:
        return await client.get('/auth/me', headers=headers)


async def test_sin_token_responde_401(entorno):
    response = await _get_me()
    assert response.status_code == 401


async def test_usuario_sin_perfiles(entorno):
    usuario, token = await entorno.usuario_con_token()

    response = await _get_me(token)

    assert response.status_code == 200
    assert response.json() == {
        'id': str(usuario.id),
        'email': 'a@a.com',
        'nombre': 'Ana',
        'apellido': 'Gomez',
        'organizador': None,
        'es_admin': False,
    }


@pytest.mark.parametrize(
    'estado',
    [EstadoOrganizador.PENDIENTE, EstadoOrganizador.APROBADO],
)
async def test_usuario_organizador_devuelve_su_estado(entorno, estado):
    usuario, token = await entorno.usuario_con_token()
    perfil = await entorno.organizadores.add(
        Organizador(
            id_organizador=uuid4(),
            id_usuario=usuario.id,
            nombre_publico='Bar Los Pinos',
            descripcion='Musica en vivo',
            estado=estado,
        )
    )

    response = await _get_me(token)

    assert response.status_code == 200
    assert response.json()['organizador'] == {
        'id_organizador': str(perfil.id_organizador),
        'nombre_publico': 'Bar Los Pinos',
        'estado': estado.value,
    }
    assert response.json()['es_admin'] is False


async def test_usuario_admin(entorno):
    usuario, token = await entorno.usuario_con_token()
    entorno.admins.add(usuario.id)

    response = await _get_me(token)

    assert response.status_code == 200
    assert response.json()['es_admin'] is True
    assert response.json()['organizador'] is None


async def test_usuario_inactivo_responde_403(entorno):
    usuario, token = await entorno.usuario_con_token()
    usuario.activo = False

    response = await _get_me(token)

    assert response.status_code == 403
