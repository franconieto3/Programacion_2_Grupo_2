from uuid import uuid4

from app.auth.events.auth_events import LoginSucceeded
from app.auth.events.publisher import AuthEventPublisher


class _Observer:
    def __init__(self) -> None:
        self.received = []

    async def handle(self, event) -> None:
        self.received.append(event)


class _BrokenObserver:
    async def handle(self, event) -> None:
        raise RuntimeError("boom")


async def test_publish_notifies_all_subscribers():
    publisher = AuthEventPublisher()
    obs1, obs2 = _Observer(), _Observer()
    publisher.subscribe(obs1)
    publisher.subscribe(obs2)

    evento = LoginSucceeded(usuario_id=uuid4(), email="a@a.com")
    await publisher.publish(evento)

    assert obs1.received == [evento]
    assert obs2.received == [evento]


async def test_publish_isolates_a_failing_observer():
    publisher = AuthEventPublisher()
    healthy = _Observer()
    publisher.subscribe(_BrokenObserver())
    publisher.subscribe(healthy)

    await publisher.publish(LoginSucceeded(usuario_id=uuid4(), email="a@a.com"))

    assert len(healthy.received) == 1


def test_get_instance_returns_the_same_object():
    AuthEventPublisher.reset_instance()

    a = AuthEventPublisher.get_instance()
    b = AuthEventPublisher.get_instance()

    assert a is b


def test_direct_construction_bypasses_the_singleton():
    fresh_a = AuthEventPublisher()
    fresh_b = AuthEventPublisher()

    assert fresh_a is not fresh_b
