import pytest

from app.auth.behaviors.email_register import EmailRegister
from app.auth.credentials import EmailRegistration
from app.auth.exceptions import EmailAlreadyRegisteredError


class _SpyObserver:
    def __init__(self) -> None:
        self.received = []

    async def handle(self, event) -> None:
        self.received.append(event)


async def test_register_creates_user_hashes_password_and_publishes_event(
    user_repository, password_hasher, event_publisher
):
    spy = _SpyObserver()
    event_publisher.subscribe(spy)
    behavior = EmailRegister(user_repository, password_hasher, event_publisher)
    credentials = EmailRegistration(
        email="a@a.com", password="secret123", nombre="Ana", apellido="Gomez"
    )

    resultado = await behavior.register(credentials)

    assert resultado.email == "a@a.com"
    assert resultado.nombre == "Ana"
    guardado = await user_repository.get_by_email("a@a.com")
    assert guardado is not None
    assert guardado.password_hash != "secret123"
    assert len(spy.received) == 1


async def test_register_rejects_duplicate_email(user_repository, password_hasher, event_publisher):
    behavior = EmailRegister(user_repository, password_hasher, event_publisher)
    credentials = EmailRegistration(
        email="a@a.com", password="secret123", nombre="Ana", apellido="Gomez"
    )
    await behavior.register(credentials)

    with pytest.raises(EmailAlreadyRegisteredError):
        await behavior.register(credentials)
