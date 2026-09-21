from functools import lru_cache

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


@lru_cache
def get_settings() -> Settings:
    """Plomeria idiomatica de FastAPI (cache de una unica instancia por proceso).

    No se cuenta como el Singleton "de ejercicio" del TP: ese rol lo cumple
    AuthEventPublisher (ver app/auth/events/publisher.py), que resuelve un problema
    de identidad real (un unico bus de eventos compartido), no solo evita relecturas
    de configuracion.
    """
    return Settings()
