"""Puerto de envio de emails (DIP): EmailNotificationObserver decide QUE mail
mandar; EmailSender decide COMO se manda (SMTP real, proveedor transaccional,
o -como hoy- log a consola para desarrollo/TP)."""

import logging
from typing import Protocol, runtime_checkable

logger = logging.getLogger(__name__)


@runtime_checkable
class EmailSender(Protocol):
    async def send(self, *, to: str, subject: str, body: str) -> None: ...


class ConsoleEmailSender:
    """Implementacion de desarrollo: loguea el email en vez de enviarlo de
    verdad. Reemplazable por una implementacion SMTP/proveedor transaccional
    sin tocar EmailNotificationObserver (OCP)."""

    async def send(self, *, to: str, subject: str, body: str) -> None:
        logger.info("EMAIL a=%s asunto=%r\n%s", to, subject, body)
