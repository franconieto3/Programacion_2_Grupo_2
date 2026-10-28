"""El composition root arma una unica cadena por proceso: si cada request
tuviera su propio geocodificador, el limite de 1 req/s y la cache no
servirian para nada."""

from app.geocodificacion.decorators.cached import CachedGeocodificador
from app.geocodificacion.dependencies import (
    cerrar_geocodificador,
    get_geocodificador,
)


async def test_devuelve_siempre_la_misma_instancia():
    try:
        primera = get_geocodificador()
        assert primera is get_geocodificador()
        assert isinstance(primera, CachedGeocodificador)
    finally:
        await cerrar_geocodificador()


async def test_cerrar_crea_una_instancia_nueva_la_proxima_vez():
    primera = get_geocodificador()
    await cerrar_geocodificador()
    try:
        assert get_geocodificador() is not primera
    finally:
        await cerrar_geocodificador()


async def test_cerrar_sin_haber_buscado_no_falla():
    await cerrar_geocodificador()
