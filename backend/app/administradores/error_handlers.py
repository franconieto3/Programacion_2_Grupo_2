"""Traduce las excepciones del dominio de administradores a respuestas HTTP,
igual que app/organizadores/error_handlers.py."""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.administradores.exceptions import NoEsAdministradorError

_STATUS_BY_EXCEPTION = {
    NoEsAdministradorError: status.HTTP_403_FORBIDDEN,
}


def register_administradores_exception_handlers(app: FastAPI) -> None:
    for exc_type, status_code in _STATUS_BY_EXCEPTION.items():

        def _handler(
            _request: Request, exc: Exception, _status_code: int = status_code
        ) -> JSONResponse:
            return JSONResponse(
                status_code=_status_code, content={'detail': str(exc)}
            )

        app.add_exception_handler(exc_type, _handler)
