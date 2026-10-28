"""Composition root del modulo de geocodificacion: el unico lugar que conoce
NominatimGeocodificador y el orden de los decorators. BuscarLugar solo ve el
Protocol Geocodificador.

A diferencia de los repositorios (uno por request), el geocodificador es
UNO POR PROCESO: el lock del limite de tasa y la cache solo sirven si todas
las requests pasan por el mismo objeto. Se usa `lru_cache`, igual que
get_settings."""

from functools import lru_cache

import httpx
from fastapi import Depends

from app.core.config import get_settings
from app.geocodificacion.decorators.cached import CachedGeocodificador
from app.geocodificacion.decorators.rate_limited import (
    RateLimitedGeocodificador,
)
from app.geocodificacion.geocodificador import (
    Geocodificador,
    NominatimGeocodificador,
)
from app.geocodificacion.service import BuscarLugar


@lru_cache
def _get_cliente_http() -> httpx.AsyncClient:
    """Compartido para reusar conexiones con Nominatim entre requests."""
    return httpx.AsyncClient()


@lru_cache
def _get_geocodificador() -> Geocodificador:
    settings = get_settings()
    nominatim = NominatimGeocodificador(
        _get_cliente_http(),
        base_url=settings.nominatim_url,
        user_agent=settings.nominatim_user_agent,
        timeout=settings.nominatim_timeout_segundos,
        countrycodes=settings.nominatim_countrycodes,
    )
    # La cache va por fuera: un acierto no consume el cupo de 1 req/s.
    return CachedGeocodificador(
        RateLimitedGeocodificador(
            nominatim, settings.nominatim_intervalo_minimo_segundos
        ),
        ttl=settings.geocodificacion_cache_ttl_segundos,
        max_entradas=settings.geocodificacion_cache_max_entradas,
    )


def get_geocodificador() -> Geocodificador:
    return _get_geocodificador()


def get_buscar_lugar(
    geocodificador: Geocodificador = Depends(get_geocodificador),
) -> BuscarLugar:
    return BuscarLugar(geocodificador)


async def cerrar_geocodificador() -> None:
    """Se llama en el shutdown de la app (app/main.py). Si nunca se busco
    un lugar, no hay cliente que cerrar."""
    if _get_cliente_http.cache_info().currsize:
        await _get_cliente_http().aclose()
    _get_geocodificador.cache_clear()
    _get_cliente_http.cache_clear()
