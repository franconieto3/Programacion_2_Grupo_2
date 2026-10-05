import pytest

from app.auth.behaviors.email_register import EmailRegister
from app.auth.behaviors.email_signin import EmailSignIn
from app.auth.credentials import EmailCredentials, EmailRegistration
from app.auth.events.auth_events import LoginFailed
from app.auth.exceptions import InactiveAccountError, InvalidCredentialsError
from app.models.usuario import RolEnum


async def _crear_usuario(
    user_repository, password_hasher, event_publisher, email="a@a.com", password="secret123"
):
    register = EmailRegister(user_repository, password_hasher, event_publisher)
    await register.register(
        EmailRegistration(email=email, password=password, nombre="Ana", rol=RolEnum.DEMANDANTE)
    )


async def test_sign_in_succeeds_with_correct_credentials(
    user_repository, password_hasher, token_service, event_publisher
):
    await _crear_usuario(user_repository, password_hasher, event_publisher)
    behavior = EmailSignIn(user_repository, password_hasher, token_service, event_publisher)

    resultado = await behavior.sign_in(EmailCredentials(email="a@a.com", password="secret123"))

    assert resultado.email == "a@a.com"
    assert resultado.access_token
    assert resultado.refresh_token


async def test_sign_in_fails_with_wrong_password(
    user_repository, password_hasher, token_service, event_publisher
):
    await _crear_usuario(user_repository, password_hasher, event_publisher)
    behavior = EmailSignIn(user_repository, password_hasher, token_service, event_publisher)

    with pytest.raises(InvalidCredentialsError):
        await behavior.sign_in(EmailCredentials(email="a@a.com", password="incorrecta"))


async def test_sign_in_fails_with_unknown_email(
    user_repository, password_hasher, token_service, event_publisher
):
    behavior = EmailSignIn(user_repository, password_hasher, token_service, event_publisher)

    with pytest.raises(InvalidCredentialsError):
        await behavior.sign_in(EmailCredentials(email="nadie@a.com", password="lo-que-sea"))


async def test_sign_in_fails_for_inactive_account(
    user_repository, password_hasher, token_service, event_publisher
):
    await _crear_usuario(user_repository, password_hasher, event_publisher)
    usuario = await user_repository.get_by_email("a@a.com")
    usuario.activo = False
    behavior = EmailSignIn(user_repository, password_hasher, token_service, event_publisher)

    with pytest.raises(InactiveAccountError):
        await behavior.sign_in(EmailCredentials(email="a@a.com", password="secret123"))


class _HasherQueNoDebeVerificar:
    async def verify(self, plain_password: str, password_hash: str) -> bool:
        raise AssertionError("no se debe verificar contra un password_hash vacio")


class _ColectorLoginFailed:
    def __init__(self) -> None:
        self.eventos: list[LoginFailed] = []

    async def handle(self, event) -> None:
        if isinstance(event, LoginFailed):
            self.eventos.append(event)


async def test_sign_in_fails_for_user_without_local_password(
    user_repository, password_hasher, token_service, event_publisher
):
    colector = _ColectorLoginFailed()
    event_publisher.subscribe(colector)
    await _crear_usuario(user_repository, password_hasher, event_publisher)
    usuario = await user_repository.get_by_email("a@a.com")
    usuario.password_hash = ""
    behavior = EmailSignIn(
        user_repository, _HasherQueNoDebeVerificar(), token_service, event_publisher
    )

    with pytest.raises(InvalidCredentialsError):
        await behavior.sign_in(EmailCredentials(email="a@a.com", password=""))

    assert [e.reason for e in colector.eventos] == ["password_incorrecta"]
