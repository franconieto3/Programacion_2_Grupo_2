import pytest

from app.auth.credentials import EmailCredentials, EmailRecoveryRequest, EmailRegistration
from app.auth.credentials_factory import CredentialsFactory
from app.auth.schemas import LoginRequest, RecoverPasswordRequest, RegisterRequest
from app.models.usuario import RolEnum


def test_create_credentials_from_register_request():
    peticion = RegisterRequest(
        email="a@a.com", password="secret123", nombre="Ana", rol=RolEnum.DEMANDANTE
    )

    credentials = CredentialsFactory.create_credentials(peticion)

    assert credentials == EmailRegistration(
        email="a@a.com", password="secret123", nombre="Ana", rol=RolEnum.DEMANDANTE
    )


def test_create_credentials_from_login_request():
    peticion = LoginRequest(email="a@a.com", password="secret123")

    credentials = CredentialsFactory.create_credentials(peticion)

    assert credentials == EmailCredentials(email="a@a.com", password="secret123")


def test_create_credentials_from_recover_password_request_has_no_password():
    peticion = RecoverPasswordRequest(email="a@a.com")

    credentials = CredentialsFactory.create_credentials(peticion)

    assert credentials == EmailRecoveryRequest(email="a@a.com")
    assert not hasattr(credentials, "password")


def test_create_credentials_rejects_unknown_type():
    with pytest.raises(TypeError):
        CredentialsFactory.create_credentials(object())  # type: ignore[call-overload]


def test_identifier_is_the_email():
    assert EmailCredentials(email="a@a.com", password="x").identifier == "a@a.com"
    assert EmailRecoveryRequest(email="a@a.com").identifier == "a@a.com"


def test_password_is_not_exposed_in_repr():
    assert "secret123" not in repr(EmailCredentials(email="a@a.com", password="secret123"))
