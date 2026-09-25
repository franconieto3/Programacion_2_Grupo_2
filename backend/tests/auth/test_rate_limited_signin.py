from datetime import timedelta
from uuid import uuid4

import pytest

from app.auth.credentials import EmailCredentials
from app.auth.decorators.rate_limited_signin import InMemoryLoginAttemptsStore, RateLimitedSignIn
from app.auth.exceptions import AccountTemporarilyLockedError, InvalidCredentialsError
from app.auth.results import AuthResult


class _AlwaysFailingSignIn:
    async def sign_in(self, credentials):
        raise InvalidCredentialsError()


class _FailsOnceThenSucceeds:
    def __init__(self) -> None:
        self.calls = 0

    async def sign_in(self, credentials):
        self.calls += 1
        if self.calls == 1:
            raise InvalidCredentialsError()
        return AuthResult(
            usuario_id=uuid4(),
            email="a@a.com",
            nombre="Ana",
            rol="DEMANDANTE",
            access_token="t",
            refresh_token="r",
        )


async def test_locks_account_after_max_attempts():
    store = InMemoryLoginAttemptsStore()
    decorated = RateLimitedSignIn(
        _AlwaysFailingSignIn(), store, max_attempts=3, lockout_window=timedelta(minutes=15)
    )
    credentials = EmailCredentials(usuario="a@a.com", password="x")

    for _ in range(3):
        with pytest.raises(InvalidCredentialsError):
            await decorated.sign_in(credentials)

    with pytest.raises(AccountTemporarilyLockedError):
        await decorated.sign_in(credentials)


async def test_successful_login_resets_the_counter():
    store = InMemoryLoginAttemptsStore()
    decorated = RateLimitedSignIn(
        _FailsOnceThenSucceeds(), store, max_attempts=3, lockout_window=timedelta(minutes=15)
    )
    credentials = EmailCredentials(usuario="a@a.com", password="x")

    with pytest.raises(InvalidCredentialsError):
        await decorated.sign_in(credentials)

    resultado = await decorated.sign_in(credentials)

    assert resultado.access_token == "t"
    assert not await store.is_locked("a@a.com", 3, timedelta(minutes=15))
