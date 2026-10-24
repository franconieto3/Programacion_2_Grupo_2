"""Traduce las excepciones del dominio de organizadores a respuestas HTTP,
igual que app/auth/error_handlers.py. Los mensajes no exponen nada sensible
(hablan del propio usuario), asi que se devuelve el de la excepcion."""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.organizadores.exceptions import (
    OrganizadorNoAprobadoError,
    OrganizadorNoEncontradoError,
    OrganizadorSuspendidoError,
    SolicitudYaExistenteError,
    TransicionEstadoInvalidaError,
)

_STATUS_BY_EXCEPTION = {
    SolicitudYaExistenteError: status.HTTP_409_CONFLICT,
    OrganizadorSuspendidoError: status.HTTP_403_FORBIDDEN,
    OrganizadorNoEncontradoError: status.HTTP_404_NOT_FOUND,
    OrganizadorNoAprobadoError: status.HTTP_403_FORBIDDEN,
    TransicionEstadoInvalidaError: status.HTTP_409_CONFLICT,
}


def register_organizadores_exception_handlers(app: FastAPI) -> None:
    for exc_type, status_code in _STATUS_BY_EXCEPTION.items():

        def _handler(
            _request: Request, exc: Exception, _status_code: int = status_code
        ) -> JSONResponse:
            return JSONResponse(
                status_code=_status_code, content={'detail': str(exc)}
            )

        app.add_exception_handler(exc_type, _handler)
