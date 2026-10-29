"""Integracion de GET /config/ubicacion-default contra la app real de
FastAPI, con Settings reemplazado via `app.dependency_overrides` (mismo
enfoque que tests/eventos/test_router_integration.py). Settings se construye
con `_env_file=None` para no depender del .env local."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import Settings, get_settings
from app.main import app


@pytest.fixture
def con_settings():
    def _usar(**valores) -> None:
        settings = Settings(_env_file=None, **valores)
        app.dependency_overrides[get_settings] = lambda: settings

    yield _usar

    app.dependency_overrides.clear()


def _client() -> AsyncClient:
    return AsyncClient(
        transport=ASGITransport(app=app), base_url='http://test'
    )


async def test_sin_token_devuelve_la_ubicacion_por_defecto(con_settings):
    con_settings()

    async with _client() as client:
        response = await client.get('/config/ubicacion-default')

    assert response.status_code == 200
    assert response.json() == {
        'nombre': 'Buenos Aires',
        'lat': -34.6037,
        'lng': -58.3816,
        'zoom': 12,
    }


async def test_refleja_la_configuracion(con_settings):
    con_settings(
        ubicacion_default_nombre='Córdoba',
        ubicacion_default_lat=-31.4201,
        ubicacion_default_lng=-64.1888,
        ubicacion_default_zoom=13,
    )

    async with _client() as client:
        response = await client.get('/config/ubicacion-default')

    assert response.status_code == 200
    assert response.json() == {
        'nombre': 'Córdoba',
        'lat': -31.4201,
        'lng': -64.1888,
        'zoom': 13,
    }
