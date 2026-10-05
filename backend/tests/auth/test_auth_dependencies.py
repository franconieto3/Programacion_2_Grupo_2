from datetime import timedelta

import pytest

from app.auth.auth import Auth
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
from app.auth.credentials import EmailCredentials, EmailRecoveryRequest
from app.auth.credentials_factory import CredentialsFactory
from app.auth.decorators.rate_limited_signin import InMemoryLoginAttemptsStore, RateLimitedSignIn
from app.auth.dependencies import get_auth
from app.auth.exceptions import PasswordRecoveryNotSupportedError
from app.auth.schemas import LoginRequest
from app.core.config import Settings


@pytest.fixture
def settings() -> Settings:
    return Settings(
        login_max_attempts=3, login_lockout_minutes=10, password_reset_token_ttl_minutes=30
    )


@pytest.fixture
def auth(
    user_repository,
    password_hasher,
    token_service,
    reset_token_repository,
    event_publisher,
    settings,
) -> Auth:
    return get_auth(
        user_repository=user_repository,
        password_hasher=password_hasher,
        token_service=token_service,
        reset_token_repository=reset_token_repository,
        event_publisher=event_publisher,
        attempts_store=InMemoryLoginAttemptsStore(),
        settings=settings,
        authorization="Bearer access-abc",
        refresh_token="refresh-xyz",
    )


def test_credentials_factory_creates_email_credentials():
    credentials = CredentialsFactory.create_credentials(
        LoginRequest(email="a@a.com", password="secret123")
    )

    assert isinstance(credentials, EmailCredentials)
    assert credentials == EmailCredentials(email="a@a.com", password="secret123")


def test_get_auth_assembles_the_email_strategies(auth):
    sign_in = auth._sign_in_behavior
    register = auth._register_behavior
    verify = auth._verify_behavior
    recovery = auth._recovery_behavior

    assert isinstance(sign_in, RateLimitedSignIn) and isinstance(sign_in, SignInBehavior)
    assert isinstance(sign_in._wrapped, EmailSignIn)
    assert isinstance(register, EmailRegister) and isinstance(register, RegisterBehavior)
    assert isinstance(verify, EmailVerify) and isinstance(verify, VerifyBehavior)
    assert isinstance(recovery, EmailRecovery) and isinstance(recovery, RecoveryBehavior)


def test_get_auth_applies_settings(auth):
    sign_in = auth._sign_in_behavior

    assert sign_in._max_attempts == 3
    assert sign_in._lockout_window == timedelta(minutes=10)
    assert auth._recovery_behavior._reset_token_ttl == timedelta(minutes=30)


def test_get_auth_extracts_session_tokens(auth):
    assert auth._verify_behavior._access_token == "access-abc"
    assert auth._verify_behavior._refresh_token == "refresh-xyz"


def test_unsupported_recovery_is_a_recovery_behavior():
    assert isinstance(UnsupportedRecovery("google"), RecoveryBehavior)


async def test_unsupported_recovery_raises_domain_error():
    credentials = EmailRecoveryRequest(email="a@gmail.com")

    with pytest.raises(PasswordRecoveryNotSupportedError) as exc_info:
        await UnsupportedRecovery("google").recover_password(credentials)

    assert exc_info.value.provider == "google"
