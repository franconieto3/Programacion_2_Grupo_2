from datetime import timedelta

from app.auth.behaviors.email_recovery import EmailRecovery
from app.auth.behaviors.email_register import EmailRegister
from app.auth.credentials import EmailRecoveryRequest, EmailRegistration
from app.auth.events.auth_events import PasswordRecoveryRequested


class _SpyObserver:
    def __init__(self) -> None:
        self.received = []

    async def handle(self, event) -> None:
        self.received.append(event)


async def test_recover_password_for_existing_user_creates_token_and_publishes_event(
    user_repository, password_hasher, event_publisher, reset_token_repository
):
    register = EmailRegister(user_repository, password_hasher, event_publisher)
    await register.register(
        EmailRegistration(email="a@a.com", password="secret123", nombre="Ana", apellido="Gomez")
    )
    spy = _SpyObserver()
    event_publisher.subscribe(spy)
    behavior = EmailRecovery(
        user_repository, reset_token_repository, event_publisher, reset_token_ttl=timedelta(minutes=30)
    )

    await behavior.recover_password(EmailRecoveryRequest(email="a@a.com"))

    assert len(reset_token_repository.created) == 1
    evento = spy.received[-1]
    assert isinstance(evento, PasswordRecoveryRequested)
    assert evento.reset_token is not None
    assert evento.usuario_id is not None


async def test_recover_password_for_unknown_email_does_not_create_token(
    user_repository, event_publisher, reset_token_repository
):
    spy = _SpyObserver()
    event_publisher.subscribe(spy)
    behavior = EmailRecovery(
        user_repository, reset_token_repository, event_publisher, reset_token_ttl=timedelta(minutes=30)
    )

    await behavior.recover_password(EmailRecoveryRequest(email="nadie@a.com"))

    assert reset_token_repository.created == []
    evento = spy.received[-1]
    assert isinstance(evento, PasswordRecoveryRequested)
    assert evento.reset_token is None
    assert evento.usuario_id is None
