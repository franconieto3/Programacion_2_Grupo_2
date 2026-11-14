"""Sin un JWT_SECRET_KEY propio la API no tiene que arrancar: con un secreto
conocido (el viejo default o el de .env.example) cualquiera puede firmar
tokens validos."""

import pytest
from pydantic import ValidationError

from app.core.config import JWT_SECRET_KEY_LARGO_MINIMO, Settings


def test_sin_jwt_secret_key_falla(monkeypatch):
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)

    with pytest.raises(ValidationError, match="JWT_SECRET_KEY"):
        Settings(_env_file=None)


@pytest.mark.parametrize(
    "secreto",
    [
        "",
        "change-me-in-.env",
        "cambiar-por-un-secreto-largo-y-aleatorio",
        "a" * (JWT_SECRET_KEY_LARGO_MINIMO - 1),
    ],
)
def test_secretos_vacios_de_ejemplo_o_cortos_se_rechazan(secreto):
    with pytest.raises(ValidationError, match="JWT_SECRET_KEY"):
        Settings(_env_file=None, jwt_secret_key=secreto)


def test_un_secreto_propio_se_acepta():
    secreto = "a" * JWT_SECRET_KEY_LARGO_MINIMO

    settings = Settings(_env_file=None, jwt_secret_key=secreto)

    assert settings.jwt_secret_key == secreto


def test_se_lee_de_la_variable_de_entorno(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", "x" * 40)

    assert Settings(_env_file=None).jwt_secret_key == "x" * 40
