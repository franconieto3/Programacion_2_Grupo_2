"""Integracion de GET /eventos/mios, PATCH /eventos/{id_evento},
POST /eventos/{id_evento}/cancelar y POST /admin/eventos/{id_evento}/ocultar
contra la app real de FastAPI, con la persistencia reemplazada por dobles en
memoria via `app.dependency_overrides`. Se recorre la cadena completa de
dependencias: get_usuario_actual (401) -> require_organizador_aprobado o
get_admin_actual (403) -> caso de uso."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.administradores.dependencies import get_administrador_repository
from app.auth.dependencies import get_token_service, get_user_repository
from app.categorias.dependencies import get_categoria_repository
from app.eventos.dependencies import get_evento_repository
from app.eventos.models import EstadoEvento
from app.main import app
from app.organizadores.dependencies import get_organizador_repository
from app.organizadores.models import EstadoOrganizador, Organizador
from tests.conftest import FakeTokenService, InMemoryUserRepository
from tests.eventos.test_gestion_eventos import (
    BAR,
    InMemoryCategoriaRepository,
    InMemoryEventoRepository,
    evento,
    organizador,
)
from tests.organizadores.test_admin_router_integration import (
    InMemoryAdministradorRepository,
)
from tests.organizadores.test_solicitar_organizador import (
    InMemoryOrganizadorRepository,
)


class Entorno:
    def __init__(self) -> None:
        self.usuarios = InMemoryUserRepository()
        self.tokens = FakeTokenService()
        self.eventos = InMemoryEventoRepository()
        self.organizadores = InMemoryOrganizadorRepository()
        self.admins = InMemoryAdministradorRepository()

    async def token(self) -> tuple[str, object]:
        usuario = await self.usuarios.create(
            email=f'{uuid4()}@a.com',
            password_hash='x',
            nombre='Ana',
            apellido='Gomez',
        )
        return self.tokens.create_access_token(usuario), usuario

    async def organizador(
        self, estado: EstadoOrganizador = EstadoOrganizador.APROBADO
    ) -> tuple[dict[str, str], Organizador]:
        token, usuario = await self.token()
        perfil = organizador()
        perfil.id_usuario = usuario.id
        perfil.estado = estado
        await self.organizadores.add(perfil)
        return {'Authorization': f'Bearer {token}'}, perfil

    async def admin(self) -> dict[str, str]:
        token, usuario = await self.token()
        self.admins.add(usuario.id)
        return {'Authorization': f'Bearer {token}'}


@pytest.fixture
def entorno():
    e = Entorno()
    overrides = {
        get_user_repository: lambda: e.usuarios,
        get_token_service: lambda: e.tokens,
        get_evento_repository: lambda: e.eventos,
        get_organizador_repository: lambda: e.organizadores,
        get_administrador_repository: lambda: e.admins,
        get_categoria_repository: lambda: InMemoryCategoriaRepository([BAR]),
    }
    app.dependency_overrides.update(overrides)

    yield e

    app.dependency_overrides.clear()


def _client() -> AsyncClient:
    return AsyncClient(
        transport=ASGITransport(app=app), base_url='http://test'
    )


ACCIONES_DE_ORGANIZADOR = [
    ('GET', '/eventos/mios', None),
    ('PATCH', f'/eventos/{uuid4()}', {'titulo': 'x'}),
    ('POST', f'/eventos/{uuid4()}/cancelar', None),
]


# --- Autenticacion y RF-01.7 ---


@pytest.mark.parametrize(('metodo', 'url', 'cuerpo'), ACCIONES_DE_ORGANIZADOR)
async def test_sin_token_responde_401(entorno, metodo, url, cuerpo):
    async with _client() as client:
        response = await client.request(metodo, url, json=cuerpo)
    assert response.status_code == 401


@pytest.mark.parametrize(('metodo', 'url', 'cuerpo'), ACCIONES_DE_ORGANIZADOR)
async def test_sin_perfil_de_organizador_responde_403(
    entorno, metodo, url, cuerpo
):
    token, _ = await entorno.token()
    async with _client() as client:
        response = await client.request(
            metodo,
            url,
            json=cuerpo,
            headers={'Authorization': f'Bearer {token}'},
        )
    assert response.status_code == 403


@pytest.mark.parametrize(('metodo', 'url', 'cuerpo'), ACCIONES_DE_ORGANIZADOR)
async def test_organizador_pendiente_responde_403(
    entorno, metodo, url, cuerpo
):
    headers, _ = await entorno.organizador(EstadoOrganizador.PENDIENTE)
    async with _client() as client:
        response = await client.request(
            metodo, url, json=cuerpo, headers=headers
        )
    assert response.status_code == 403


# --- GET /eventos/mios ---


async def test_mis_eventos_devuelve_los_propios_con_su_estado(entorno):
    headers, yo = await entorno.organizador()
    cancelado = await entorno.eventos.add(
        evento(yo, estado=EstadoEvento.CANCELADO)
    )
    await entorno.eventos.add(evento(organizador()))

    async with _client() as client:
        response = await client.get('/eventos/mios', headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert [e['id_evento'] for e in body] == [str(cancelado.id_evento)]
    assert body[0]['estado'] == 'CANCELADO'


# --- PATCH /eventos/{id_evento} ---


async def test_editar_evento_propio_responde_200(entorno):
    headers, yo = await entorno.organizador()
    original = await entorno.eventos.add(evento(yo))

    async with _client() as client:
        response = await client.patch(
            f'/eventos/{original.id_evento}',
            json={
                'titulo': 'Nuevo titulo',
                'fecha_inicio': '2026-11-22T21:00:00-03:00',
                'categorias': ['bar'],
            },
            headers=headers,
        )

    assert response.status_code == 200
    body = response.json()
    assert body['titulo'] == 'Nuevo titulo'
    assert datetime.fromisoformat(body['fecha_inicio']) == datetime(
        2026, 11, 23, 0, 0, tzinfo=timezone.utc
    )
    assert [c['slug'] for c in body['categorias']] == ['bar']


async def test_editar_evento_ajeno_responde_403(entorno):
    headers, _ = await entorno.organizador()
    ajeno = await entorno.eventos.add(evento(organizador()))

    async with _client() as client:
        response = await client.patch(
            f'/eventos/{ajeno.id_evento}',
            json={'titulo': 'x'},
            headers=headers,
        )

    assert response.status_code == 403
    assert ajeno.titulo == 'Recital en la plaza'


async def test_editar_evento_inexistente_responde_404(entorno):
    headers, _ = await entorno.organizador()

    async with _client() as client:
        response = await client.patch(
            f'/eventos/{uuid4()}', json={'titulo': 'x'}, headers=headers
        )

    assert response.status_code == 404


async def test_editar_evento_cancelado_responde_409(entorno):
    headers, yo = await entorno.organizador()
    original = await entorno.eventos.add(
        evento(yo, estado=EstadoEvento.CANCELADO)
    )

    async with _client() as client:
        response = await client.patch(
            f'/eventos/{original.id_evento}',
            json={'titulo': 'x'},
            headers=headers,
        )

    assert response.status_code == 409


@pytest.mark.parametrize(
    'cuerpo',
    [
        {'titulo': None},
        {'categorias': ['inexistente']},
        {'fecha_fin': '2026-11-20T00:00:00Z'},  # antes del inicio
        {'lugar': {'latitud': -34.6}},
    ],
)
async def test_editar_con_datos_invalidos_responde_422(entorno, cuerpo):
    headers, yo = await entorno.organizador()
    original = await entorno.eventos.add(evento(yo))

    async with _client() as client:
        response = await client.patch(
            f'/eventos/{original.id_evento}', json=cuerpo, headers=headers
        )

    assert response.status_code == 422


# --- POST /eventos/{id_evento}/cancelar ---


async def test_cancelar_evento_propio_responde_200(entorno):
    headers, yo = await entorno.organizador()
    original = await entorno.eventos.add(evento(yo))

    async with _client() as client:
        response = await client.post(
            f'/eventos/{original.id_evento}/cancelar', headers=headers
        )

    assert response.status_code == 200
    assert response.json()['estado'] == 'CANCELADO'
    assert original.estado == EstadoEvento.CANCELADO


async def test_cancelar_evento_ajeno_responde_403(entorno):
    headers, _ = await entorno.organizador()
    ajeno = await entorno.eventos.add(evento(organizador()))

    async with _client() as client:
        response = await client.post(
            f'/eventos/{ajeno.id_evento}/cancelar', headers=headers
        )

    assert response.status_code == 403
    assert ajeno.estado == EstadoEvento.PUBLICADO


async def test_cancelar_evento_ya_cancelado_responde_409(entorno):
    headers, yo = await entorno.organizador()
    original = await entorno.eventos.add(
        evento(yo, estado=EstadoEvento.CANCELADO)
    )

    async with _client() as client:
        response = await client.post(
            f'/eventos/{original.id_evento}/cancelar', headers=headers
        )

    assert response.status_code == 409


# --- POST /admin/eventos/{id_evento}/ocultar ---


async def test_ocultar_sin_token_responde_401(entorno):
    async with _client() as client:
        response = await client.post(f'/admin/eventos/{uuid4()}/ocultar')
    assert response.status_code == 401


async def test_ocultar_sin_ser_admin_responde_403(entorno):
    headers, yo = await entorno.organizador()
    original = await entorno.eventos.add(evento(yo))

    async with _client() as client:
        response = await client.post(
            f'/admin/eventos/{original.id_evento}/ocultar', headers=headers
        )

    assert response.status_code == 403
    assert original.estado == EstadoEvento.PUBLICADO


async def test_admin_oculta_un_evento_responde_200(entorno):
    headers = await entorno.admin()
    original = await entorno.eventos.add(evento(None))

    async with _client() as client:
        response = await client.post(
            f'/admin/eventos/{original.id_evento}/ocultar', headers=headers
        )

    assert response.status_code == 200
    assert response.json()['estado'] == 'OCULTO'
    assert original.estado == EstadoEvento.OCULTO


async def test_ocultar_evento_inexistente_responde_404(entorno):
    headers = await entorno.admin()

    async with _client() as client:
        response = await client.post(
            f'/admin/eventos/{uuid4()}/ocultar', headers=headers
        )

    assert response.status_code == 404


async def test_ocultar_evento_ya_oculto_responde_409(entorno):
    headers = await entorno.admin()
    original = await entorno.eventos.add(
        evento(None, estado=EstadoEvento.OCULTO)
    )

    async with _client() as client:
        response = await client.post(
            f'/admin/eventos/{original.id_evento}/ocultar', headers=headers
        )

    assert response.status_code == 409
