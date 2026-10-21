"""Traduce las excepciones del dominio de eventos a respuestas HTTP, igual
que app/organizadores/error_handlers.py."""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.eventos.exceptions import TransicionEstadoEventoInvalidaError

_STATUS_BY_EXCEPTION = {
    TransicionEstadoEventoInvalidaError: status.HTTP_409_CONFLICT,
}


def register_eventos_exception_handlers(app: FastAPI) -> None:
    for exc_type, status_code in _STATUS_BY_EXCEPTION.items():

        def _handler(
            _request: Request, exc: Exception, _status_code: int = status_code
        ) -> JSONResponse:
            return JSONResponse(
                status_code=_status_code, content={'detail': str(exc)}
            )

        app.add_exception_handler(exc_type, _handler)
