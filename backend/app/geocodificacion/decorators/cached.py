"""Decorator: cachea en memoria las busquedas de CUALQUIER Geocodificador
(RNF-01.4), sin modificar NominatimGeocodificador (OCP).

Va por fuera de RateLimitedGeocodificador en el composition root, asi un
acierto de cache responde al instante y no consume el cupo de 1 req/s.

Cachea tambien las busquedas sin resultados (tambien son llamadas evitables),
pero no los errores: la excepcion se propaga y la proxima busqueda vuelve a
intentar. Misma limitacion que el rate limit: la cache es por proceso."""

import time
from collections import OrderedDict
from collections.abc import Callable

from app.geocodificacion.geocodificador import Geocodificador, LugarEncontrado

_Clave = tuple[str, int]


class CachedGeocodificador:
    def __init__(
        self,
        envuelto: Geocodificador,
        ttl: float,
        max_entradas: int,
        *,
        reloj: Callable[[], float] = time.monotonic,
    ) -> None:
        self._envuelto = envuelto
        self._ttl = ttl
        self._max_entradas = max_entradas
        self._reloj = reloj
        # Ordenado por momento de guardado: la primera es la mas vieja.
        self._entradas: OrderedDict[
            _Clave, tuple[float, list[LugarEncontrado]]
        ] = OrderedDict()

    async def buscar(
        self, consulta: str, limite: int
    ) -> list[LugarEncontrado]:
        clave = (consulta.casefold(), limite)
        ahora = self._reloj()

        entrada = self._entradas.get(clave)
        if entrada is not None:
            guardado_en, lugares = entrada
            if ahora - guardado_en < self._ttl:
                return list(lugares)
            del self._entradas[clave]

        lugares = await self._envuelto.buscar(consulta, limite)
        self._guardar(clave, lugares)
        return list(lugares)

    def _guardar(self, clave: _Clave, lugares: list[LugarEncontrado]) -> None:
        self._entradas.pop(clave, None)
        self._entradas[clave] = (self._reloj(), list(lugares))
        while len(self._entradas) > self._max_entradas:
            self._entradas.popitem(last=False)
