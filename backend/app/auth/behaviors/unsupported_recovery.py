"""UnsupportedRecovery implements RecoveryBehavior[Credentials] (Null Object).

Los proveedores OAuth (Google, Facebook) no gestionan contrasenas locales, asi
que la recuperacion de contrasena no aplica. En vez de inyectar `None` en
`Auth` (y obligarlo a chequearlo antes de delegar), la dependencia que arme
el Auth de esos proveedores inyecta esta estrategia, que cumple el mismo
contrato y responde con una excepcion de dominio clara (traducida a HTTP en
app/auth/error_handlers.py). Acepta cualquier `Credentials`, asi que sirve
como RecoveryBehavior de cualquier proveedor.
"""

from app.auth.credentials import Credentials
from app.auth.exceptions import PasswordRecoveryNotSupportedError


class UnsupportedRecovery:
    def __init__(self, provider: str) -> None:
        self._provider = provider

    async def recover_password(self, credentials: Credentials) -> None:
        raise PasswordRecoveryNotSupportedError(self._provider)
