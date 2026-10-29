"""RateLimitedGeocodificador con reloj y sleep falsos: se verifica cuanto
espera sin dormir de verdad."""

import asyncio

import pytest

from app.geocodificacion.decorators.rate_limited import (
    RateLimitedGeocodificador,
)
from app.geocodificacion.geocodificador import LugarEncontrado


class RelojFalso:
    """`dormir` adelanta el reloj, como pasaria con un sleep real."""

    def __init__(self) -> None:
        self.ahora = 100.0
        self.esperas: list[float] = []

    def __call__(self) -> float:
        return self.ahora

    async def dormir(self, segundos: float) -> None:
        self.esperas.append(segundos)
        self.ahora += segundos


class GeocodificadorFalso:
    def __init__(self, reloj: RelojFalso) -> None:
        self._reloj = reloj
        self.inicios: list[float] = []

    async def buscar(
        self, consulta: str, limite: int
    ) -> list[LugarEncontrado]:
        self.inicios.append(self._reloj())
        await asyncio.sleep(0)
        return []


@pytest.fixture
def reloj() -> RelojFalso:
    return RelojFalso()


@pytest.fixture
def envuelto(reloj) -> GeocodificadorFalso:
    return GeocodificadorFalso(reloj)


@pytest.fixture
def geocodificador(reloj, envuelto) -> RateLimitedGeocodificador:
    return RateLimitedGeocodificador(
        envuelto, 1.0, reloj=reloj, dormir=reloj.dormir
    )


async def test_la_primera_busqueda_no_espera(geocodificador, reloj):
    await geocodificador.buscar('Mar del Plata', 5)
    assert reloj.esperas == []


async def test_dos_busquedas_seguidas_quedan_separadas_un_segundo(
    geocodificador, reloj, envuelto
):
    await geocodificador.buscar('Mar del Plata', 5)
    reloj.ahora += 0.3
    await geocodificador.buscar('Rosario', 5)

    assert reloj.esperas == [pytest.approx(0.7)]
    assert envuelto.inicios[1] - envuelto.inicios[0] == pytest.approx(1.0)


async def test_si_ya_paso_el_intervalo_no_espera(geocodificador, reloj):
    await geocodificador.buscar('Mar del Plata', 5)
    reloj.ahora += 1.5
    await geocodificador.buscar('Rosario', 5)

    assert reloj.esperas == []


async def test_busquedas_concurrentes_salen_de_a_una_por_segundo(
    geocodificador, envuelto
):
    await asyncio.gather(
        *(geocodificador.buscar(f'consulta {i}', 5) for i in range(4))
    )

    separaciones = [
        b - a
        for a, b in zip(envuelto.inicios, envuelto.inicios[1:], strict=False)
    ]
    assert len(envuelto.inicios) == 4
    assert separaciones == [pytest.approx(1.0)] * 3
