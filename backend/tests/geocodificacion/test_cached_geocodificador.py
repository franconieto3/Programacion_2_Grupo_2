import pytest

from app.geocodificacion.decorators.cached import CachedGeocodificador
from app.geocodificacion.exceptions import GeocodificadorNoDisponibleError
from app.geocodificacion.geocodificador import LugarEncontrado

_LUGAR = LugarEncontrado(
    nombre='Mar del Plata',
    tipo='city',
    lat=-38.0,
    lng=-57.55,
    lat_min=-38.1,
    lat_max=-37.9,
    lng_min=-57.7,
    lng_max=-57.5,
)


class RelojFalso:
    def __init__(self) -> None:
        self.ahora = 0.0

    def __call__(self) -> float:
        return self.ahora


class GeocodificadorQueCuenta:
    def __init__(self) -> None:
        self.llamadas: list[tuple[str, int]] = []
        self.fallar = False

    async def buscar(
        self, consulta: str, limite: int
    ) -> list[LugarEncontrado]:
        self.llamadas.append((consulta, limite))
        if self.fallar:
            raise GeocodificadorNoDisponibleError()
        return [_LUGAR]


@pytest.fixture
def reloj() -> RelojFalso:
    return RelojFalso()


@pytest.fixture
def envuelto() -> GeocodificadorQueCuenta:
    return GeocodificadorQueCuenta()


def _cache(envuelto, reloj, ttl=60.0, max_entradas=10):
    return CachedGeocodificador(
        envuelto, ttl=ttl, max_entradas=max_entradas, reloj=reloj
    )


async def test_la_misma_busqueda_consulta_una_sola_vez(envuelto, reloj):
    cache = _cache(envuelto, reloj)

    primera = await cache.buscar('Mar del Plata', 5)
    segunda = await cache.buscar('MAR DEL PLATA', 5)

    assert primera == segunda == [_LUGAR]
    assert envuelto.llamadas == [('Mar del Plata', 5)]


async def test_distinto_limite_es_otra_entrada(envuelto, reloj):
    cache = _cache(envuelto, reloj)

    await cache.buscar('Mar del Plata', 5)
    await cache.buscar('Mar del Plata', 3)

    assert len(envuelto.llamadas) == 2


async def test_vencido_el_ttl_vuelve_a_consultar(envuelto, reloj):
    cache = _cache(envuelto, reloj, ttl=60.0)

    await cache.buscar('Mar del Plata', 5)
    reloj.ahora = 59.0
    await cache.buscar('Mar del Plata', 5)
    reloj.ahora = 61.0
    await cache.buscar('Mar del Plata', 5)

    assert len(envuelto.llamadas) == 2


async def test_los_errores_no_se_cachean(envuelto, reloj):
    cache = _cache(envuelto, reloj)
    envuelto.fallar = True

    with pytest.raises(GeocodificadorNoDisponibleError):
        await cache.buscar('Mar del Plata', 5)

    envuelto.fallar = False
    assert await cache.buscar('Mar del Plata', 5) == [_LUGAR]
    assert len(envuelto.llamadas) == 2


async def test_supera_max_entradas_desaloja_la_mas_vieja(envuelto, reloj):
    cache = _cache(envuelto, reloj, max_entradas=2)

    await cache.buscar('uno', 5)
    await cache.buscar('dos', 5)
    await cache.buscar('tres', 5)
    await cache.buscar('dos', 5)  # sigue en cache
    await cache.buscar('uno', 5)  # fue desalojada

    assert [c for c, _ in envuelto.llamadas] == ['uno', 'dos', 'tres', 'uno']


async def test_modificar_el_resultado_no_altera_la_cache(envuelto, reloj):
    cache = _cache(envuelto, reloj)

    resultado = await cache.buscar('Mar del Plata', 5)
    resultado.clear()

    assert await cache.buscar('Mar del Plata', 5) == [_LUGAR]
