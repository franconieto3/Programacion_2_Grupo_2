from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# HS256 firma con HMAC-SHA256: un secreto de al menos 32 bytes (256 bits).
JWT_SECRET_KEY_LARGO_MINIMO = 32

# Valores que circulan en el repositorio (el viejo default y el de
# .env.example): nunca pueden ser el secreto real.
_SECRETOS_DE_EJEMPLO = frozenset({
    "change-me-in-.env",
    "cambiar-por-un-secreto-largo-y-aleatorio",
})


class Settings(BaseSettings):
    """Configuracion de la aplicacion, cargada desde variables de entorno / .env."""

    # hide_input_in_errors: un valor invalido no se imprime en el error de
    # arranque (quedaria en los logs del proveedor). Importa para
    # JWT_SECRET_KEY y para DATABASE_URL, que lleva la contrasena de la base.
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        hide_input_in_errors=True,
    )

    # RNF-05.2: dev y produccion usan el mismo motor (PostgreSQL); SQLite
    # solo esta admitido para la suite de tests automatizados, y ahi se
    # sobreescribe via la variable de entorno DATABASE_URL
    # (sqlite+aiosqlite:///./test.db o :memory:), nunca aca como default.
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/eventos"

    # Sin valor por defecto utilizable: con un secreto conocido cualquiera
    # puede firmar tokens validos. Si falta, es corto o es uno de los valores
    # de ejemplo, el arranque falla (ver _validar_jwt_secret_key).
    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    access_token_ttl_minutes: int = 15
    refresh_token_ttl_days: int = 14
    password_reset_token_ttl_minutes: int = 60

    cookie_domain: str | None = None
    cookie_secure: bool = True

    login_max_attempts: int = 5
    login_lockout_minutes: int = 15

    # Zona con la que se calcula la hora local de inicio de un evento
    # (Evento.hora_inicio_local), usada por el filtro horario (RF-03.5).
    zona_horaria: str = 'America/Argentina/Buenos_Aires'

    # RF-03.8: donde se abre el mapa si el usuario rechaza el permiso de
    # geolocalizacion (GET /config/ubicacion-default). Validados: un .env
    # mal cargado hace fallar el arranque en vez de centrar el mapa en
    # cualquier lado.
    ubicacion_default_nombre: str = 'Buenos Aires'
    ubicacion_default_lat: float = Field(default=-34.6037, ge=-90, le=90)
    ubicacion_default_lng: float = Field(default=-58.3816, ge=-180, le=180)
    ubicacion_default_zoom: int = Field(default=12, ge=0, le=19)

    # RNF-05.1: la politica de uso de Nominatim pide como maximo 1 request
    # por segundo y un User-Agent que identifique a la aplicacion (idealmente
    # con un contacto real; completarlo en el .env).
    nominatim_url: str = 'https://nominatim.openstreetmap.org'
    nominatim_user_agent: str = 'eventos-api/0.1 (TP Programacion 2)'
    nominatim_intervalo_minimo_segundos: float = 1.0
    nominatim_timeout_segundos: float = 5.0
    # Codigos ISO separados por coma (ej. "ar") para acotar los resultados;
    # vacio = sin restriccion.
    nominatim_countrycodes: str | None = None
    # Zona que se prioriza sin excluir el resto (viewbox de Nominatim, sin
    # `bounded`): "lng_oeste,lat_norte,lng_este,lat_sur". Por defecto,
    # Argentina: "Cordoba" o "San Martin" devuelven primero los de aca, pero
    # "Montevideo" se sigue encontrando. Vacio = sin prioridad.
    nominatim_viewbox: str | None = '-73.6,-21.7,-53.5,-55.1'

    # RNF-01.4: cache local de busquedas de lugares.
    geocodificacion_cache_ttl_segundos: float = 86400
    geocodificacion_cache_max_entradas: int = 1000

    @field_validator("jwt_secret_key")
    @classmethod
    def _validar_jwt_secret_key(cls, valor: str) -> str:
        corto = len(valor) < JWT_SECRET_KEY_LARGO_MINIMO
        if corto or valor in _SECRETOS_DE_EJEMPLO:
            raise ValueError(
                "JWT_SECRET_KEY no esta definida, es un valor de ejemplo "
                f"o tiene menos de {JWT_SECRET_KEY_LARGO_MINIMO} "
                "caracteres. Generar una con: python -c "
                '"import secrets; print(secrets.token_urlsafe(48))"'
            )
        return valor


@lru_cache
def get_settings() -> Settings:
    """Plomeria idiomatica de FastAPI (cache de una unica instancia por proceso).

    No se cuenta como el Singleton "de ejercicio" del TP: ese rol lo cumple
    AuthEventPublisher (ver app/auth/events/publisher.py), que resuelve un problema
    de identidad real (un unico bus de eventos compartido), no solo evita relecturas
    de configuracion.
    """
    return Settings()
