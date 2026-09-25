"""UnsupportedRecovery implements RecoveryBehavior (Null Object).

Los proveedores OAuth (Google, Facebook) no gestionan contrasenas locales, asi
que la recuperacion de contrasena no aplica. En vez de inyectar `None` en
`Auth` (y obligarlo a chequearlo antes de delegar), las fabricas de esas
familias inyectan esta estrategia, que cumple el mismo contrato y responde con
una excepcion de dominio clara (traducida a HTTP en app/auth/error_handlers.py).
"""

from app.auth.credentials import Credentials
from app.auth.exceptions import PasswordRecoveryNotSupportedError


class UnsupportedRecovery:
    def __init__(self, provider: str) -> None:
        self._provider = provider

    async def recover_password(self, credentials: Credentials) -> None:
        raise PasswordRecoveryNotSupportedError(self._provider)
