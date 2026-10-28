"""Decorator: agrega el limite de tasa de RNF-05.1 (Nominatim admite como
maximo 1 request por segundo) a CUALQUIER Geocodificador, sin modificar
NominatimGeocodificador (OCP), igual que RateLimitedSignIn con
SignInBehavior.

No rechaza la request que llega antes de tiempo: la hace esperar lo que falta
para cumplir el intervalo. Con el debounce del buscador del frontend las
esperas son cortas, y un 429 propio obligaria al usuario a reintentar a mano.

Limitacion conocida (la misma que InMemoryLoginAttemptsStore): el estado vive
en el proceso, asi que con `uvicorn --workers > 1` cada worker tendria su
propio limite. Aceptable para el TP, que corre un unico proceso."""

import asyncio
import time
from collections.abc import Awaitable, Callable

from app.geocodificacion.geocodificador import Geocodificador, LugarEncontrado


class RateLimitedGeocodificador:
    def __init__(
        self,
        envuelto: Geocodificador,
        intervalo_minimo: float = 1.0,
        *,
        reloj: Callable[[], float] = time.monotonic,
        dormir: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        self._envuelto = envuelto
        self._intervalo_minimo = intervalo_minimo
        self._reloj = reloj
        self._dormir = dormir
        self._lock = asyncio.Lock()
        self._ultimo_envio: float | None = None

    async def buscar(
        self, consulta: str, limite: int
    ) -> list[LugarEncontrado]:
        await self._esperar_turno()
        return await self._envuelto.buscar(consulta, limite)

    async def _esperar_turno(self) -> None:
        """El lock serializa solo la reserva del turno, no la request: el
        siguiente en la cola puede ir esperando su segundo mientras la
        anterior todavia esta en vuelo. Lo que se garantiza es que entre dos
        INICIOS de request pase al menos `intervalo_minimo`."""
        async with self._lock:
            if self._ultimo_envio is not None:
                transcurrido = self._reloj() - self._ultimo_envio
                faltante = self._intervalo_minimo - transcurrido
                if faltante > 0:
                    await self._dormir(faltante)
            self._ultimo_envio = self._reloj()
