from datetime import timedelta

import pytest

from app.auth.behaviors.base import (
    RecoveryBehavior,
    RegisterBehavior,
    SignInBehavior,
    VerifyBehavior,
)
from app.auth.behaviors.email_recovery import EmailRecovery
from app.auth.behaviors.email_register import EmailRegister
from app.auth.behaviors.email_signin import EmailSignIn
from app.auth.behaviors.email_verify import EmailVerify
from app.auth.behaviors.unsupported_recovery import UnsupportedRecovery
from app.auth.credentials import EmailCredentials
from app.auth.exceptions import PasswordRecoveryNotSupportedError
from app.auth.factories import AuthProviderFactory, EmailAuthFactory
from app.auth.schemas import LoginRequest


@pytest.fixture
def email_factory(
    user_repository, password_hasher, token_service, reset_token_repository, event_publisher
) -> EmailAuthFactory:
    return EmailAuthFactory(
        user_repository,
        password_hasher,
        token_service,
        reset_token_repository,
        event_publisher,
        reset_token_ttl=timedelta(minutes=30),
    )


def test_email_factory_implements_auth_provider_factory(email_factory):
    assert isinstance(email_factory, AuthProviderFactory)


def test_email_factory_creates_email_credentials(email_factory):
    credentials = email_factory.create_credentials(
        LoginRequest(email="a@a.com", password="secret123")
    )

    assert isinstance(credentials, EmailCredentials)
    assert credentials.get_credentials() == {"usuario": "a@a.com", "password": "secret123"}


def test_email_factory_creates_the_email_family(email_factory):
    sign_in = email_factory.create_sign_in_behavior()
    register = email_factory.create_register_behavior()
    verify = email_factory.create_verify_behavior()
    recovery = email_factory.create_recovery_behavior()

    assert isinstance(sign_in, EmailSignIn) and isinstance(sign_in, SignInBehavior)
    assert isinstance(register, EmailRegister) and isinstance(register, RegisterBehavior)
    assert isinstance(verify, EmailVerify) and isinstance(verify, VerifyBehavior)
    assert isinstance(recovery, EmailRecovery) and isinstance(recovery, RecoveryBehavior)


def test_unsupported_recovery_is_a_recovery_behavior():
    assert isinstance(UnsupportedRecovery("google"), RecoveryBehavior)


async def test_unsupported_recovery_raises_domain_error():
    credentials = EmailCredentials(usuario="a@gmail.com")

    with pytest.raises(PasswordRecoveryNotSupportedError) as exc_info:
        await UnsupportedRecovery("google").recover_password(credentials)

    assert exc_info.value.provider == "google"
