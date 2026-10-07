"""Contratos HTTP (Pydantic) de la API de autenticacion. Separados de
app/auth/results.py: estos son DTOs de entrada/salida del router, no objetos
de dominio usados por Auth/las estrategias (DIP: el dominio no conoce Pydantic
ni el router)."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    nombre: str = Field(min_length=1, max_length=255)
    apellido: str = Field(min_length=1, max_length=255)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class RecoverPasswordRequest(BaseModel):
    email: EmailStr


class UsuarioPublic(BaseModel):
    id: UUID
    email: str
    nombre: str
    apellido: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioPublic


class SessionInfoResponse(BaseModel):
    usuario_id: UUID
    email: str
    expires_at: datetime | None
    access_token: str | None = Field(
        default=None,
        description="Presente solo cuando la sesion se resolvio via refresh token (silent refresh).",
    )


class GenericMessageResponse(BaseModel):
    message: str
