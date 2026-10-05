"""EmailRecovery implements RecoveryBehavior[EmailRecoveryRequest].

Para este flujo solo se conoce el email, por eso recibe
`EmailRecoveryRequest` (sin contrasena) en vez de `EmailCredentials`.
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from app.auth.credentials import EmailRecoveryRequest
from app.auth.events.auth_events import PasswordRecoveryRequested
from app.auth.events.publisher import AuthEventPublisher
from app.auth.repository import UserRepository
from app.auth.token_repository import PasswordResetTokenRepository


class EmailRecovery:
    def __init__(
        self,
        user_repository: UserRepository,
        reset_token_repository: PasswordResetTokenRepository,
        event_publisher: AuthEventPublisher,
        reset_token_ttl: timedelta,
    ) -> None:
        self._user_repository = user_repository
        self._reset_token_repository = reset_token_repository
        self._event_publisher = event_publisher
        self._reset_token_ttl = reset_token_ttl

    async def recover_password(self, credentials: EmailRecoveryRequest) -> None:
        email = credentials.email

        usuario = await self._user_repository.get_by_email(email)

        # Se genera y hashea el token SIEMPRE, exista o no la cuenta, para que
        # el costo de CPU de esta rama no delate por timing si el email esta
        # registrado (mitigacion parcial de enumeracion de usuarios; el I/O de
        # persistencia solo ocurre si el usuario existe).
        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

        if usuario is not None:
            expires_at = datetime.now(timezone.utc) + self._reset_token_ttl
            await self._reset_token_repository.create(usuario.id, token_hash, expires_at)

        # La respuesta HTTP es identica en ambos casos (ver router): el
        # evento solo lleva el token crudo cuando la cuenta existe, para que
        # EmailNotificationObserver no mande nada si no hay a quien mandarle.
        await self._event_publisher.publish(
            PasswordRecoveryRequested(
                email=email,
                usuario_id=usuario.id if usuario is not None else None,
                reset_token=raw_token if usuario is not None else None,
            )
        )
