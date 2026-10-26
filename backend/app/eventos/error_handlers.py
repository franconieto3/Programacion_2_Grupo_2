"""Traduce las excepciones del dominio de eventos a respuestas HTTP, igual
que app/organizadores/error_handlers.py."""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.eventos.exceptions import (
    CategoriasInvalidasError,
    EventoNoEditableError,
    EventoNoEncontradoError,
    FechasEventoInvalidasError,
    NoEsDuenioDelEventoError,
    TransicionEstadoEventoInvalidaError,
)

_STATUS_BY_EXCEPTION = {
    TransicionEstadoEventoInvalidaError: status.HTTP_409_CONFLICT,
    EventoNoEncontradoError: status.HTTP_404_NOT_FOUND,
    NoEsDuenioDelEventoError: status.HTTP_403_FORBIDDEN,
    EventoNoEditableError: status.HTTP_409_CONFLICT,
    CategoriasInvalidasError: status.HTTP_422_UNPROCESSABLE_CONTENT,
    FechasEventoInvalidasError: status.HTTP_422_UNPROCESSABLE_CONTENT,
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
