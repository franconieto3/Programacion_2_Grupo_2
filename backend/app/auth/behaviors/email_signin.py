"""EmailSignIn implements SignInBehavior[EmailCredentials], tal como el diagrama."""

from app.auth.credentials import EmailCredentials
from app.auth.events.auth_events import LoginFailed, LoginSucceeded
from app.auth.events.publisher import AuthEventPublisher
from app.auth.exceptions import InactiveAccountError, InvalidCredentialsError
from app.auth.repository import UserRepository
from app.auth.results import AuthResult
from app.core.security.password_hasher import PasswordHasher
from app.core.security.token_service import TokenService


class EmailSignIn:
    def __init__(
        self,
        user_repository: UserRepository,
        password_hasher: PasswordHasher,
        token_service: TokenService,
        event_publisher: AuthEventPublisher,
    ) -> None:
        self._user_repository = user_repository
        self._password_hasher = password_hasher
        self._token_service = token_service
        self._event_publisher = event_publisher

    async def sign_in(self, credentials: EmailCredentials) -> AuthResult:
        email = credentials.email
        password = credentials.password

        usuario = await self._user_repository.get_by_email(email)
        if usuario is None:
            await self._event_publisher.publish(
                LoginFailed(email=email, reason="usuario_inexistente")
            )
            raise InvalidCredentialsError()

        # Un usuario sin contrasena local (ej. registrado via un proveedor
        # externo) no puede autenticarse por email + contrasena.
        if not usuario.password_hash or not await self._password_hasher.verify(
            password, usuario.password_hash
        ):
            await self._event_publisher.publish(
                LoginFailed(email=email, reason="password_incorrecta")
            )
            raise InvalidCredentialsError()

        # El chequeo de cuenta activa va DESPUES de validar la contrasena: asi
        # "cuenta inactiva" solo se revela a quien ya demostro conocerla, sin
        # convertirse en un vector de enumeracion de cuentas.
        if not usuario.activo:
            await self._event_publisher.publish(
                LoginFailed(email=email, reason="cuenta_inactiva")
            )
            raise InactiveAccountError()

        access_token = self._token_service.create_access_token(usuario)
        refresh_token = await self._token_service.issue_refresh_token(usuario.id)

        await self._event_publisher.publish(
            LoginSucceeded(usuario_id=usuario.id, email=usuario.email)
        )

        return AuthResult(
            usuario_id=usuario.id,
            email=usuario.email,
            nombre=usuario.nombre,
            apellido=usuario.apellido,
            access_token=access_token,
            refresh_token=refresh_token,
        )
