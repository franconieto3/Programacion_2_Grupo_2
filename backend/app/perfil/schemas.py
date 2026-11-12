from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.auth.schemas import UsuarioPublic
from app.organizadores.models import EstadoOrganizador


class OrganizadorResumen(BaseModel):
    """Lo minimo del perfil de organizador para que el frontend decida que
    ofrecer: con PENDIENTE muestra la solicitud en curso, con APROBADO
    habilita "Crear evento" y "Mis eventos" (RF-01.6, RF-01.7)."""

    model_config = ConfigDict(from_attributes=True)

    id_organizador: UUID
    nombre_publico: str
    estado: EstadoOrganizador


class UsuarioActualResponse(UsuarioPublic):
    """Respuesta de GET /auth/me. `organizador` es None si el usuario nunca
    solicito el perfil."""

    organizador: OrganizadorResumen | None
    es_admin: bool
