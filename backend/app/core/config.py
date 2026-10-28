from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuracion de la aplicacion, cargada desde variables de entorno / .env."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # RNF-05.2: dev y produccion usan el mismo motor (PostgreSQL); SQLite
    # solo esta admitido para la suite de tests automatizados, y ahi se
    # sobreescribe via la variable de entorno DATABASE_URL
    # (sqlite+aiosqlite:///./test.db o :memory:), nunca aca como default.
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/eventos"

    jwt_secret_key: str = "change-me-in-.env"
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

    # RNF-01.4: cache local de busquedas de lugares.
    geocodificacion_cache_ttl_segundos: float = 86400
    geocodificacion_cache_max_entradas: int = 1000


@lru_cache
def get_settings() -> Settings:
    """Plomeria idiomatica de FastAPI (cache de una unica instancia por proceso).

    No se cuenta como el Singleton "de ejercicio" del TP: ese rol lo cumple
    AuthEventPublisher (ver app/auth/events/publisher.py), que resuelve un problema
    de identidad real (un unico bus de eventos compartido), no solo evita relecturas
    de configuracion.
    """
    return Settings()
