import pytest

from app.auth.credentials import EmailCredentials
from app.auth.credentials_factory import CredentialsFactory
from app.auth.schemas import LoginRequest, RecoverPasswordRequest, RegisterRequest
from app.models.usuario import RolEnum


def test_create_credentials_from_register_request():
    peticion = RegisterRequest(
        email="a@a.com", password="secret123", nombre="Ana", rol=RolEnum.DEMANDANTE
    )

    credentials = CredentialsFactory.create_credentials(peticion)

    assert isinstance(credentials, EmailCredentials)
    assert credentials.get_credentials() == {
        "usuario": "a@a.com",
        "password": "secret123",
        "nombre": "Ana",
        "rol": RolEnum.DEMANDANTE,
    }


def test_create_credentials_from_login_request():
    peticion = LoginRequest(email="a@a.com", password="secret123")

    data = CredentialsFactory.create_credentials(peticion).get_credentials()

    assert data == {"usuario": "a@a.com", "password": "secret123"}


def test_create_credentials_from_recover_password_request_has_no_password():
    peticion = RecoverPasswordRequest(email="a@a.com")

    data = CredentialsFactory.create_credentials(peticion).get_credentials()

    assert data == {"usuario": "a@a.com", "password": None}


def test_create_credentials_rejects_unknown_type():
    with pytest.raises(TypeError):
        CredentialsFactory.create_credentials(object())  # type: ignore[arg-type]
