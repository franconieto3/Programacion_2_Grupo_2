"""Puerto de geocodificacion (DIP): BuscarLugar solo conoce Geocodificador
(Protocol); NominatimGeocodificador es la implementacion concreta y vive
detras del composition root (app/geocodificacion/dependencies.py), envuelta
por los decorators de cache y limite de tasa (app/geocodificacion/decorators).

Nominatim por si solo no respeta nada de RNF-05.1: el limite de 1 req/s y la
cache los agregan los decorators, sin tocar esta clase (OCP)."""

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

import httpx

from app.geocodificacion.exceptions import GeocodificadorNoDisponibleError


@dataclass(frozen=True)
class LugarEncontrado:
    """Una sugerencia de lugar. El bounding box usa los mismos nombres que
    el viewport de GET /eventos (lat_min, lat_max, lng_min, lng_max), para
    que el frontend pueda buscar eventos en el lugar elegido sin traducir
    nada (CU-02)."""

    nombre: str
    tipo: str | None
    lat: float
    lng: float
    lat_min: float
    lat_max: float
    lng_min: float
    lng_max: float


@runtime_checkable
class Geocodificador(Protocol):
    async def buscar(
        self, consulta: str, limite: int
    ) -> list[LugarEncontrado]: ...


class NominatimGeocodificador:
    """Cliente de GET /search de Nominatim. Recibe el httpx.AsyncClient ya
    creado para reusar conexiones entre requests; quien lo crea (el
    composition root) es quien lo cierra."""

    def __init__(
        self,
        cliente: httpx.AsyncClient,
        *,
        base_url: str,
        user_agent: str,
        timeout: float,
        countrycodes: str | None = None,
    ) -> None:
        self._cliente = cliente
        self._url = f'{base_url.rstrip("/")}/search'
        self._user_agent = user_agent
        self._timeout = timeout
        self._countrycodes = countrycodes

    async def buscar(
        self, consulta: str, limite: int
    ) -> list[LugarEncontrado]:
        params = {
            'q': consulta,
            'format': 'jsonv2',
            'limit': limite,
            'accept-language': 'es',
        }
        if self._countrycodes:
            params['countrycodes'] = self._countrycodes

        try:
            response = await self._cliente.get(
                self._url,
                params=params,
                # RNF-05.1: la politica de Nominatim exige identificarse.
                headers={'User-Agent': self._user_agent},
                timeout=self._timeout,
            )
            # 429 / 403 son la forma en que Nominatim avisa que se excedio
            # su politica de uso: se tratan igual que una caida.
            response.raise_for_status()
            return [_a_lugar(item) for item in response.json()]
        except (httpx.HTTPError, ValueError, KeyError, IndexError) as exc:
            raise GeocodificadorNoDisponibleError() from exc


def _a_lugar(item: dict) -> LugarEncontrado:
    """Nominatim devuelve coordenadas como strings y el boundingbox como
    [sur, norte, oeste, este]."""
    sur, norte, oeste, este = (float(v) for v in item['boundingbox'])
    return LugarEncontrado(
        nombre=item['display_name'],
        tipo=item.get('type'),
        lat=float(item['lat']),
        lng=float(item['lon']),
        lat_min=sur,
        lat_max=norte,
        lng_min=oeste,
        lng_max=este,
    )
