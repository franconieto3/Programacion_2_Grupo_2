"""Integracion de GET /geocodificacion/buscar contra la app real de FastAPI,
con el geocodificador reemplazado por un doble via `app.dependency_overrides`
(mismo enfoque que tests/eventos/test_router_integration.py): nunca se
llama a Nominatim."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.auth.dependencies import get_token_service, get_user_repository
from app.geocodificacion.dependencies import get_geocodificador
from app.geocodificacion.exceptions import GeocodificadorNoDisponibleError
from app.geocodificacion.geocodificador import LugarEncontrado
from app.main import app
from tests.conftest import FakeTokenService, InMemoryUserRepository

_LUGAR = LugarEncontrado(
    nombre='Mar del Plata, Buenos Aires',
    tipo='city',
    lat=-38.0,
    lng=-57.55,
    lat_min=-38.1,
    lat_max=-37.9,
    lng_min=-57.7,
    lng_max=-57.5,
)


class GeocodificadorFalso:
    def __init__(self) -> None:
        self.lugares: list[LugarEncontrado] = [_LUGAR]
        self.fallar = False
        self.llamadas: list[tuple[str, int]] = []

    async def buscar(
        self, consulta: str, limite: int
    ) -> list[LugarEncontrado]:
        self.llamadas.append((consulta, limite))
        if self.fallar:
            raise GeocodificadorNoDisponibleError()
        return self.lugares


@pytest.fixture
def wired_app():
    user_repository = InMemoryUserRepository()
    token_service = FakeTokenService()
    geocodificador = GeocodificadorFalso()

    app.dependency_overrides[get_user_repository] = lambda: user_repository
    app.dependency_overrides[get_token_service] = lambda: token_service
    app.dependency_overrides[get_geocodificador] = lambda: geocodificador

    yield user_repository, token_service, geocodificador

    app.dependency_overrides.clear()


def _client() -> AsyncClient:
    return AsyncClient(
        transport=ASGITransport(app=app), base_url='http://test'
    )


async def _headers(user_repository, token_service) -> dict[str, str]:
    usuario = await user_repository.create(
        email='a@a.com', password_hash='x', nombre='Ana', apellido='Gomez'
    )
    token = token_service.create_access_token(usuario)
    return {'Authorization': f'Bearer {token}'}


async def test_buscar_sin_token_responde_401(wired_app):
    async with _client() as client:
        response = await client.get('/geocodificacion/buscar?q=Mar del Plata')
    assert response.status_code == 401


async def test_buscar_devuelve_lugares_con_su_viewport(wired_app):
    user_repository, token_service, geocodificador = wired_app
    headers = await _headers(user_repository, token_service)

    async with _client() as client:
        response = await client.get(
            '/geocodificacion/buscar',
            params={'q': '  Mar   del Plata ', 'limit': 3},
            headers=headers,
        )

    assert response.status_code == 200
    assert response.json() == [
        {
            'nombre': 'Mar del Plata, Buenos Aires',
            'tipo': 'city',
            'lat': -38.0,
            'lng': -57.55,
            'lat_min': -38.1,
            'lat_max': -37.9,
            'lng_min': -57.7,
            'lng_max': -57.5,
        }
    ]
    assert geocodificador.llamadas == [('Mar del Plata', 3)]


async def test_sin_coincidencias_devuelve_lista_vacia(wired_app):
    user_repository, token_service, geocodificador = wired_app
    headers = await _headers(user_repository, token_service)
    geocodificador.lugares = []

    async with _client() as client:
        response = await client.get(
            '/geocodificacion/buscar', params={'q': 'xyzxyz'}, headers=headers
        )

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.parametrize(
    'params',
    [{'q': 'ab'}, {}, {'q': 'Mar del Plata', 'limit': 11}],
)
async def test_parametros_invalidos_responden_422(wired_app, params):
    user_repository, token_service, _ = wired_app
    headers = await _headers(user_repository, token_service)

    async with _client() as client:
        response = await client.get(
            '/geocodificacion/buscar', params=params, headers=headers
        )

    assert response.status_code == 422


async def test_geocodificador_caido_responde_503(wired_app):
    user_repository, token_service, geocodificador = wired_app
    headers = await _headers(user_repository, token_service)
    geocodificador.fallar = True

    async with _client() as client:
        response = await client.get(
            '/geocodificacion/buscar',
            params={'q': 'Mar del Plata'},
            headers=headers,
        )

    assert response.status_code == 503
    assert 'no esta disponible' in response.json()['detail']
