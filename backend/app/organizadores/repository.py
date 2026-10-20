"""Puerto de persistencia de organizadores (DIP): los servicios solo conocen
OrganizadorRepository (Protocol); SQLAlchemyOrganizadorRepository es la
implementacion concreta y vive detras del composition root
(app/organizadores/dependencies.py)."""

from typing import Protocol, runtime_checkable
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.organizadores.exceptions import SolicitudYaExistenteError
from app.organizadores.models import EstadoOrganizador, Organizador


@runtime_checkable
class OrganizadorRepository(Protocol):
    async def get_by_usuario_id(
        self, usuario_id: UUID
    ) -> Organizador | None: ...

    async def add(self, organizador: Organizador) -> Organizador: ...

    async def list_by_estado(
        self, estado: EstadoOrganizador
    ) -> list[Organizador]: ...


class SQLAlchemyOrganizadorRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_usuario_id(self, usuario_id: UUID) -> Organizador | None:
        result = await self._session.execute(
            select(Organizador).where(Organizador.id_usuario == usuario_id)
        )
        return result.scalar_one_or_none()

    async def add(self, organizador: Organizador) -> Organizador:
        """El flush ejecuta el INSERT dentro del request: asigna los defaults
        y hace saltar aca la violacion de UNIQUE sobre id_usuario (dos
        solicitudes simultaneas del mismo usuario), en vez de al commit. Esa
        violacion se traduce a SolicitudYaExistenteError para que el servicio
        no dependa de SQLAlchemy.

        No hace falta un metodo update: los cambios sobre una entidad ya
        cargada (por ejemplo, reenviar una solicitud RECHAZADA) los persiste
        la sesion al hacer commit."""
        self._session.add(organizador)
        try:
            await self._session.flush()
        except IntegrityError as exc:
            raise SolicitudYaExistenteError() from exc
        return organizador

    async def list_by_estado(
        self, estado: EstadoOrganizador
    ) -> list[Organizador]:
        """Las mas antiguas primero: el administrador revisa las solicitudes
        en el orden en que llegaron."""
        result = await self._session.execute(
            select(Organizador)
            .where(Organizador.estado == estado)
            .order_by(Organizador.fecha_creacion)
        )
        return list(result.scalars().all())
