class GeocodificacionError(Exception):
    """Base de todas las excepciones del dominio de geocodificacion."""


class GeocodificadorNoDisponibleError(GeocodificacionError):
    """Nominatim no respondio, respondio con error (incluido 429 por exceso
    de uso) o devolvio algo que no se pudo interpretar."""

    def __init__(self) -> None:
        super().__init__(
            'El servicio de busqueda de lugares no esta disponible. '
            'Intenta de nuevo en unos segundos.'
        )
