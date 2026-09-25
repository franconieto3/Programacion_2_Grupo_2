"""Observer concreto: manda mails transaccionales reaccionando a eventos de
auth. No sabe nada de SQLAlchemy, JWT ni de las estrategias que publicaron el
evento (SRP)."""

from app.auth.events.auth_events import (
    AuthEvent,
    PasswordRecoveryRequested,
    UserRegistered,
)
from app.core.email_sender import EmailSender

_RESET_LINK_BASE = "https://app.example.com/reset-password"  # TODO: mover a Settings


class EmailNotificationObserver:
    def __init__(self, email_sender: EmailSender) -> None:
        self._email_sender = email_sender

    async def handle(self, event: AuthEvent) -> None:
        if isinstance(event, UserRegistered):
            await self._email_sender.send(
                to=event.email,
                subject="Bienvenido/a a la plataforma de eventos",
                body=f"Hola {event.nombre}, tu cuenta fue creada correctamente.",
            )
        elif isinstance(event, PasswordRecoveryRequested):
            if event.reset_token is None:
                return  # el email no existe: no se manda nada, ver mitigacion de enumeracion
            link = f"{_RESET_LINK_BASE}?token={event.reset_token}"
            await self._email_sender.send(
                to=event.email,
                subject="Recuperar contrasena",
                body=f"Usa este link para elegir una contrasena nueva (vence en poco tiempo): {link}",
            )
        # LoginSucceeded, LoginFailed y SessionVerified no generan email hoy;
        # este observer solo reacciona a los eventos que le interesan (OCP:
        # agregar una notificacion nueva es un elif mas, sin tocar las
        # estrategias que publican).
