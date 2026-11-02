"""Integracion de GET /eventos y GET /categorias contra la app real de
FastAPI, con la persistencia reemplazada por dobles en memoria via
`app.dependency_overrides` (mismo enfoque que
tests/organizadores/test_admin_router_integration.py)."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.auth.dependencies import get_token_service, get_user_repository
from app.categorias.dependencies import get_categoria_repository
from app.categorias.models import Categoria
from app.eventos.dependencies import get_evento_repository
from app.eventos.models import EstadoEvento, Evento, Lugar, OrigenEvento
from app.eventos.schemas import BusquedaEventosParams
from app.main import app
from tests.conftest import FakeTokenService, InMemoryUserRepository


class InMemoryEventoRepository:
    """Devuelve los eventos cargados tal cual: la regla de visibilidad y los
    filtros se prueban contra SQLite en test_sqlalchemy_evento_repository."""

    def __init__(self) -> None:
        self.eventos: list[Evento] = []
        self.ultimos_filtros: BusquedaEventosParams | None = None

    async def buscar(
        self, filtros: BusquedaEventosParams, ahora: datetime
    ) -> tuple[list[Evento], int]:
        self.ultimos_filtros = filtros
        pagina = self.eventos[filtros.offset : filtros.offset + filtros.limit]
        return pagina, len(self.eventos)


class InMemoryCategoriaRepository:
    def __init__(self, categorias: list[Categoria]) -> None:
        self._categorias = categorias

    async def list_activas(self) -> list[Categoria]:
        return [c for c in self._categorias if c.activa]

    async def get_activas_by_slugs(self, slugs: list[str]) -> list[Categoria]:
        return [c for c in self._categorias if c.activa and c.slug in slugs]


@pytest.fixture
def wired_app():
    user_repository = InMemoryUserRepository()
    token_service = FakeTokenService()
    evento_repo = InMemoryEventoRepository()
    categoria_repo = InMemoryCategoriaRepository([
        Categoria(slug='bar', nombre='Bar', activa=True),
        Categoria(slug='cine', nombre='Cine', activa=False),
    ])

    app.dependency_overrides[get_user_repository] = lambda: user_repository
    app.dependency_overrides[get_token_service] = lambda: token_service
    app.dependency_overrides[get_evento_repository] = lambda: evento_repo
    app.dependency_overrides[get_categoria_repository] = lambda: categoria_repo

    yield user_repository, token_service, evento_repo

    app.dependency_overrides.clear()


def _client() -> AsyncClient:
    return AsyncClient(
        transport=ASGITransport(app=app), base_url='http://test'
    )


async def _token(user_repository, token_service) -> str:
    usuario = await user_repository.create(
        email='a@a.com', password_hash='x', nombre='Ana', apellido='Gomez'
    )
    return token_service.create_access_token(usuario)


def _evento() -> Evento:
    return Evento(
        id_evento=uuid4(),
        id_organizador=None,
        titulo='Recital en la plaza',
        descripcion='Musica en vivo',
        fecha_inicio=datetime(2026, 11, 21, 0, 30, tzinfo=timezone.utc),
        fecha_fin=None,
        precio=None,
        estado=EstadoEvento.PUBLICADO,
        origen=OrigenEvento.SEED_EQUIPO,
        lugar=Lugar(
            id_lugar=uuid4(), nombre='Plaza', latitud=-34.6, longitud=-58.4
        ),
        categorias=[Categoria(slug='recital', nombre='Recital')],
    )


async def test_buscar_sin_token_responde_401(wired_app):
    async with _client() as client:
        response = await client.get('/eventos')
    assert response.status_code == 401


async def test_buscar_devuelve_pagina_de_eventos(wired_app):
    user_repository, token_service, evento_repo = wired_app
    token = await _token(user_repository, token_service)
    evento = _evento()
    evento_repo.eventos.append(evento)

    async with _client() as client:
        response = await client.get(
            '/eventos', headers={'Authorization': f'Bearer {token}'}
        )

    assert response.status_code == 200
    body = response.json()
    assert body['total'] == 1
    assert body['limit'] == 20
    assert body['offset'] == 0
    assert body['items'][0]['id_evento'] == str(evento.id_evento)
    assert body['items'][0]['lugar']['latitud'] == -34.6
    assert body['items'][0]['categorias'][0]['slug'] == 'recital'


async def test_buscar_recibe_todos_los_parametros(wired_app):
    user_repository, token_service, evento_repo = wired_app
    token = await _token(user_repository, token_service)

    async with _client() as client:
        response = await client.get(
            '/eventos?lat_min=-35&lat_max=-34&lng_min=-59&lng_max=-58'
            '&desde=2026-11-20&hasta=2026-11-30'
            '&hora_desde=20:00&hora_hasta=23:30'
            '&categorias=bar&categorias=teatro&limit=50&offset=10',
            headers={'Authorization': f'Bearer {token}'},
        )

    assert response.status_code == 200
    filtros = evento_repo.ultimos_filtros
    assert filtros.lat_min == -35
    assert filtros.categorias == ['bar', 'teatro']
    assert str(filtros.hora_hasta) == '23:30:00'
    assert filtros.limit == 50
    assert filtros.offset == 10


@pytest.mark.parametrize(
    'query',
    [
        'limit=101',
        'limit=0',
        'offset=-1',
        'lat_min=91',
        'lat_min=-35&lat_max=-34',
        'lat_min=-34&lat_max=-35&lng_min=-59&lng_max=-58',
        'lat_min=-35&lat_max=-34&lng_min=-58&lng_max=-59',
        'desde=2026-11-30&hasta=2026-11-20',
    ],
)
async def test_buscar_parametro_invalido_responde_422(wired_app, query):
    user_repository, token_service, _ = wired_app
    token = await _token(user_repository, token_service)

    async with _client() as client:
        response = await client.get(
            f'/eventos?{query}', headers={'Authorization': f'Bearer {token}'}
        )
    assert response.status_code == 422


async def test_listar_categorias_es_publico_y_excluye_inactivas(wired_app):
    async with _client() as client:
        response = await client.get('/categorias')

    assert response.status_code == 200
    assert [c['slug'] for c in response.json()] == ['bar']

