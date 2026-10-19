from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field

class SolicitudOrganizadorRequest(BaseModel):
    nombre_publico: str
    descripcion: str

class OrganizadorPublic(BaseModel):
    id_organizador: UUID
    id_usuario: UUID
    nombre_publico: str
    descripcion: str
    estado: str
    fecha_creacion: datetime