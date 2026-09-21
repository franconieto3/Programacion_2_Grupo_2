class AuthError(Exception):
    """Base de todas las excepciones del dominio de autenticacion."""


class InvalidCredentialsError(AuthError):
    """Email inexistente o contrasena incorrecta. Nunca se distingue cual de
    las dos al usuario final, para no habilitar enumeracion de cuentas."""


class InactiveAccountError(AuthError):
    """La cuenta existe pero fue desactivada (moderacion / baja logica)."""


class EmailAlreadyRegisteredError(AuthError):
    def __init__(self, email: str) -> None:
        super().__init__(f"El email {email!r} ya esta registrado")
        self.email = email


class AccountTemporarilyLockedError(AuthError):
    """Levantada por el decorator RateLimitedSignIn tras superar el maximo de
    intentos fallidos configurado (mitigacion de fuerza bruta, RNF-04)."""

    def __init__(self, usuario: str) -> None:
        super().__init__(f"Cuenta {usuario!r} bloqueada temporalmente por intentos fallidos")
        self.usuario = usuario


class SessionNotFoundError(AuthError):
    """No llego ni access token ni refresh token utilizable en la request."""


class InvalidTokenError(AuthError):
    """El token (access o refresh) es invalido, fue revocado o no corresponde
    a ningun usuario activo."""


class TokenExpiredError(AuthError):
    """El token es valido en forma pero ya vencio."""
