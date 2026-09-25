"""Subject del patron Observer + unico Singleton "de ejercicio" del modulo.

Por que esto es un Singleton real y no forzado: Auth y las estrategias se
instancian una vez por request (necesitan el/los token(s) de esa request
inyectados, ver EmailVerify). El publisher, en cambio, tiene que ser el mismo
objeto en todas las requests, porque los observers se suscriben una unica vez
en el arranque de la app (app/main.py). Si el publisher fuera per-request, los
observers registrados en el startup se perderian en cada request nueva.

Se implementa con un `get_instance()` clasico (no sobrescribiendo __new__)
para no romper la testabilidad: el constructor sigue disponible para crear
instancias descartables en tests unitarios/aislados, y `reset_instance()` es
el escape hatch explicito para los pocos tests de integracion que si dependen
del singleton real.
"""

import logging
from typing import Protocol, runtime_checkable

from app.auth.events.auth_events import AuthEvent

logger = logging.getLogger(__name__)


@runtime_checkable
class AuthObserver(Protocol):
    async def handle(self, event: AuthEvent) -> None: ...


class AuthEventPublisher:
    _instance: "AuthEventPublisher | None" = None

    def __init__(self) -> None:
        self._observers: list[AuthObserver] = []

    @classmethod
    def get_instance(cls) -> "AuthEventPublisher":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Solo para tests de integracion que dependan del singleton global."""
        cls._instance = None

    def subscribe(self, observer: AuthObserver) -> None:
        self._observers.append(observer)

    async def publish(self, event: AuthEvent) -> None:
        """Notifica a cada observer secuencialmente, aislando fallos: un
        observer roto (ej. SMTP caido) nunca debe tumbar el flujo de auth que
        disparo el evento. Se espera cada handler (no fire-and-forget con
        asyncio.create_task sin referencia) para que el resultado sea
        determinista en tests y no dependa de que el event loop siga vivo el
        tiempo suficiente."""
        for observer in list(self._observers):
            try:
                await observer.handle(event)
            except Exception:
                logger.exception("Observer %r fallo procesando %r", observer, event)
