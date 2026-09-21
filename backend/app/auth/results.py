"""Objetos de resultado del dominio de autenticacion.

Se mantienen separados de app/auth/schemas.py (contratos HTTP/Pydantic) para que
Auth y las estrategias no dependan de los DTOs de la capa API (DIP): el router
es quien traduce estos resultados a las respuestas HTTP.
"""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class AuthResult:
    """Resultado de un login exitoso (incluye tokens)."""

    usuario_id: UUID
    email: str
    nombre: str
    rol: str
    access_token: str
    refresh_token: str


@dataclass(frozen=True, slots=True)
class RegisteredUser:
    """Resultado de un registro exitoso. Sin tokens a proposito: el contrato
    del endpoint POST /auth/register responde 201 con los datos del usuario
    creado, no hace auto-login (RF-01.1 y RF-01.3 son flujos separados)."""

    usuario_id: UUID
    email: str
    nombre: str
    rol: str


@dataclass(frozen=True, slots=True)
class SessionInfo:
    """Resultado de verify-session."""

    usuario_id: UUID
    email: str
    rol: str
    expires_at: datetime | None
    refreshed_access_token: str | None = None


@dataclass(frozen=True, slots=True)
class AccessTokenPayload:
    sub: UUID
    email: str
    rol: str
    exp: datetime
