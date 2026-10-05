"""EmailRegister implements RegisterBehavior[EmailRegistration], tal como el diagrama."""

from app.auth.credentials import EmailRegistration
from app.auth.events.auth_events import UserRegistered
from app.auth.events.publisher import AuthEventPublisher
from app.auth.exceptions import EmailAlreadyRegisteredError
from app.auth.repository import UserRepository
from app.auth.results import RegisteredUser
from app.core.security.password_hasher import PasswordHasher


class EmailRegister:
    def __init__(
        self,
        user_repository: UserRepository,
        password_hasher: PasswordHasher,
        event_publisher: AuthEventPublisher,
    ) -> None:
        self._user_repository = user_repository
        self._password_hasher = password_hasher
        self._event_publisher = event_publisher

    async def register(self, credentials: EmailRegistration) -> RegisteredUser:
        email = credentials.email
        password = credentials.password
        nombre = credentials.nombre
        rol = credentials.rol

        if await self._user_repository.get_by_email(email) is not None:
            raise EmailAlreadyRegisteredError(email)

        password_hash = await self._password_hasher.hash(password)
        usuario = await self._user_repository.create(
            email=email, password_hash=password_hash, nombre=nombre, rol=rol
        )

        # Se publica DESPUES de crear el usuario: nunca notificar un alta que
        # todavia podria fallar (ej. por una constraint de unicidad no
        # detectada por el chequeo previo bajo una carrera concurrente).
        await self._event_publisher.publish(
            UserRegistered(usuario_id=usuario.id, email=usuario.email, nombre=usuario.nombre)
        )

        return RegisteredUser(
            usuario_id=usuario.id, email=usuario.email, nombre=usuario.nombre, rol=usuario.rol
        )
