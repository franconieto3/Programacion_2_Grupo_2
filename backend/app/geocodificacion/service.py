from app.geocodificacion.geocodificador import Geocodificador, LugarEncontrado
from app.geocodificacion.schemas import BusquedaLugarParams


class BuscarLugar:
    """Sugerencias de lugares para el buscador de ubicacion alternativa
    (CU-02). El limite de tasa (RNF-05.1) y la cache (RNF-01.4) no son
    responsabilidad de este servicio: los aporta el Geocodificador que le
    inyecta el composition root."""

    def __init__(self, geocodificador: Geocodificador) -> None:
        self._geocodificador = geocodificador

    async def ejecutar(
        self, params: BusquedaLugarParams
    ) -> list[LugarEncontrado]:
        # "  mar   del plata " y "mar del plata" son la misma busqueda: se
        # normaliza antes de llegar a la cache para no gastar dos requests.
        consulta = ' '.join(params.q.split())
        return await self._geocodificador.buscar(consulta, params.limit)
