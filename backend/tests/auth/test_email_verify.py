import pytest

from app.auth.behaviors.email_register import EmailRegister
from app.auth.behaviors.email_signin import EmailSignIn
from app.auth.behaviors.email_verify import EmailVerify
from app.auth.credentials import EmailCredentials, EmailRegistration
from app.auth.exceptions import SessionNotFoundError


async def _crear_y_loguear(user_repository, password_hasher, token_service, event_publisher):
    register = EmailRegister(user_repository, password_hasher, event_publisher)
    await register.register(
        EmailRegistration(email="a@a.com", password="secret123", nombre="Ana", apellido="Gomez")
    )
    usuario = await user_repository.get_by_email("a@a.com")
    token_service.register_user(usuario)
    signin = EmailSignIn(user_repository, password_hasher, token_service, event_publisher)
    return await signin.sign_in(EmailCredentials(email="a@a.com", password="secret123"))


async def test_verify_session_with_valid_access_token(
    user_repository, password_hasher, token_service, event_publisher
):
    resultado_login = await _crear_y_loguear(user_repository, password_hasher, token_service, event_publisher)
    behavior = EmailVerify(token_service, event_publisher, resultado_login.access_token, None)

    sesion = await behavior.verify_session()

    assert sesion.email == "a@a.com"
    assert sesion.refreshed_access_token is None


async def test_verify_session_with_refresh_token_issues_new_access_token(
    user_repository, password_hasher, token_service, event_publisher
):
    resultado_login = await _crear_y_loguear(user_repository, password_hasher, token_service, event_publisher)
    behavior = EmailVerify(token_service, event_publisher, None, resultado_login.refresh_token)

    sesion = await behavior.verify_session()

    assert sesion.email == "a@a.com"
    assert sesion.refreshed_access_token is not None


async def test_verify_session_without_any_token_raises(token_service, event_publisher):
    behavior = EmailVerify(token_service, event_publisher, None, None)

    with pytest.raises(SessionNotFoundError):
        await behavior.verify_session()
