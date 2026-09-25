"""EmailVerify implements VerifyBehavior, tal como el diagrama:
`verifySession()` no recibe argumentos.

La sesion a verificar se resuelve por INYECCION EN EL CONSTRUCTOR, no como
parametro del metodo: FastAPI construye una instancia nueva de EmailVerify
(y de Auth) por request via Depends, habiendo extraido ya el access token
(header Authorization) y/o el refresh token (cookie httpOnly) de esa request.
Ver app/auth/dependencies.py.
"""

from app.auth.events.auth_events import SessionVerified
from app.auth.events.publisher import AuthEventPublisher
from app.auth.exceptions import SessionNotFoundError
from app.auth.results import SessionInfo
from app.core.security.token_service import TokenService


class EmailVerify:
    def __init__(
        self,
        token_service: TokenService,
        event_publisher: AuthEventPublisher,
        access_token: str | None,
        refresh_token: str | None,
    ) -> None:
        self._token_service = token_service
        self._event_publisher = event_publisher
        self._access_token = access_token
        self._refresh_token = refresh_token

    async def verify_session(self) -> SessionInfo:
        if self._access_token:
            payload = self._token_service.decode_access_token(self._access_token)
            await self._event_publisher.publish(
                SessionVerified(usuario_id=payload.sub, email=payload.email, via_refresh=False)
            )
            return SessionInfo(
                usuario_id=payload.sub,
                email=payload.email,
                rol=payload.rol,
                expires_at=payload.exp,
            )

        if self._refresh_token:
            usuario = await self._token_service.resolve_refresh_token(self._refresh_token)
            nuevo_access_token = self._token_service.create_access_token(usuario)
            await self._event_publisher.publish(
                SessionVerified(usuario_id=usuario.id, email=usuario.email, via_refresh=True)
            )
            return SessionInfo(
                usuario_id=usuario.id,
                email=usuario.email,
                rol=usuario.rol,
                expires_at=None,
                refreshed_access_token=nuevo_access_token,
            )

        raise SessionNotFoundError()
