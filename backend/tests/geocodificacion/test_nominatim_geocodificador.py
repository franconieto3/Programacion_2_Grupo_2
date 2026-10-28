"""NominatimGeocodificador contra httpx.MockTransport: nunca sale a la red,
pero se ejercita el request real que armaria el cliente."""

import httpx
import pytest

from app.geocodificacion.exceptions import GeocodificadorNoDisponibleError
from app.geocodificacion.geocodificador import (
    LugarEncontrado,
    NominatimGeocodificador,
)

_MAR_DEL_PLATA = {
    'display_name': 'Mar del Plata, General Pueyrredon, Buenos Aires',
    'type': 'city',
    'lat': '-38.0033',
    'lon': '-57.5528',
    'boundingbox': ['-38.1', '-37.9', '-57.7', '-57.5'],
}


def _geocodificador(
    handler, countrycodes: str | None = None
) -> NominatimGeocodificador:
    cliente = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return NominatimGeocodificador(
        cliente,
        base_url='https://nominatim.test/',
        user_agent='eventos-api-test/1.0 (test@example.com)',
        timeout=5.0,
        countrycodes=countrycodes,
    )


async def test_manda_user_agent_y_parametros_esperados():
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=[])

    await _geocodificador(handler, countrycodes='ar').buscar(
        'Mar del Plata', 3
    )

    (request,) = requests
    assert request.url.path == '/search'
    assert request.headers['User-Agent'] == (
        'eventos-api-test/1.0 (test@example.com)'
    )
    assert request.url.params['q'] == 'Mar del Plata'
    assert request.url.params['format'] == 'jsonv2'
    assert request.url.params['limit'] == '3'
    assert request.url.params['accept-language'] == 'es'
    assert request.url.params['countrycodes'] == 'ar'


async def test_sin_countrycodes_no_manda_el_parametro():
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=[])

    await _geocodificador(handler).buscar('Mar del Plata', 3)

    assert 'countrycodes' not in requests[0].url.params


async def test_convierte_la_respuesta_a_lugares():
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[_MAR_DEL_PLATA])

    lugares = await _geocodificador(handler).buscar('Mar del Plata', 5)

    assert lugares == [
        LugarEncontrado(
            nombre='Mar del Plata, General Pueyrredon, Buenos Aires',
            tipo='city',
            lat=-38.0033,
            lng=-57.5528,
            lat_min=-38.1,
            lat_max=-37.9,
            lng_min=-57.7,
            lng_max=-57.5,
        )
    ]


async def test_sin_coincidencias_devuelve_lista_vacia():
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[])

    assert await _geocodificador(handler).buscar('xyzxyz', 5) == []


@pytest.mark.parametrize('status_code', [403, 429, 500, 503])
async def test_respuesta_con_error_es_no_disponible(status_code):
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code)

    with pytest.raises(GeocodificadorNoDisponibleError):
        await _geocodificador(handler).buscar('Mar del Plata', 5)


async def test_timeout_es_no_disponible():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout('timeout', request=request)

    with pytest.raises(GeocodificadorNoDisponibleError):
        await _geocodificador(handler).buscar('Mar del Plata', 5)


async def test_respuesta_malformada_es_no_disponible():
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[{'display_name': 'sin coords'}])

    with pytest.raises(GeocodificadorNoDisponibleError):
        await _geocodificador(handler).buscar('Mar del Plata', 5)
