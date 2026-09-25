"""Traduce las excepciones del dominio de auth (app/auth/exceptions.py) a
respuestas HTTP. Centralizado aca (en vez de try/except repetido en cada
endpoint de app/auth/router.py) para que el router se limite a orquestar
AuthProviderFactory + Auth + la respuesta de exito."""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.auth.exceptions import (
    AccountTemporarilyLockedError,
    EmailAlreadyRegisteredError,
    InactiveAccountError,
    InvalidCredentialsError,
    InvalidTokenError,
    PasswordRecoveryNotSupportedError,
    SessionNotFoundError,
    TokenExpiredError,
)

_STATUS_BY_EXCEPTION = {
    InvalidCredentialsError: status.HTTP_401_UNAUTHORIZED,
    InactiveAccountError: status.HTTP_403_FORBIDDEN,
    AccountTemporarilyLockedError: status.HTTP_423_LOCKED,
    EmailAlreadyRegisteredError: status.HTTP_409_CONFLICT,
    SessionNotFoundError: status.HTTP_401_UNAUTHORIZED,
    InvalidTokenError: status.HTTP_401_UNAUTHORIZED,
    TokenExpiredError: status.HTTP_401_UNAUTHORIZED,
    PasswordRecoveryNotSupportedError: status.HTTP_400_BAD_REQUEST,
}

_GENERIC_MESSAGE_BY_EXCEPTION = {
    InvalidCredentialsError: "Email o contrasena incorrectos.",
    InactiveAccountError: "La cuenta esta inactiva.",
    AccountTemporarilyLockedError: "Demasiados intentos fallidos. Intenta mas tarde.",
    EmailAlreadyRegisteredError: "El email ya esta registrado.",
    SessionNotFoundError: "No hay una sesion activa.",
    InvalidTokenError: "La sesion no es valida. Inicia sesion nuevamente.",
    TokenExpiredError: "La sesion expiro. Inicia sesion nuevamente.",
    PasswordRecoveryNotSupportedError: (
        "Esta cuenta usa un proveedor externo (Google/Facebook): "
        "recupera el acceso desde ese proveedor."
    ),
}


def register_auth_exception_handlers(app: FastAPI) -> None:
    for exc_type, status_code in _STATUS_BY_EXCEPTION.items():

        def _handler(
            _request: Request, exc: Exception, _status_code: int = status_code
        ) -> JSONResponse:
            message = _GENERIC_MESSAGE_BY_EXCEPTION.get(type(exc), str(exc))
            return JSONResponse(status_code=_status_code, content={"detail": message})

        app.add_exception_handler(exc_type, _handler)
