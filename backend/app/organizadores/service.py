from uuid import UUID

from app.models.usuario import Usuario
from app.organizadores.exceptions import (
    OrganizadorNoEncontradoError,
    OrganizadorSuspendidoError,
    SolicitudYaExistenteError,
)
from app.organizadores.models import EstadoOrganizador, Organizador
from app.organizadores.repository import OrganizadorRepository
from app.organizadores.schemas import SolicitudOrganizadorRequest


class SolicitarOrganizador:
    """CU-04: un usuario solicita convertirse en organizador. La solicitud
    queda PENDIENTE hasta que un administrador la apruebe o rechace."""

    def __init__(self, repo: OrganizadorRepository) -> None:
        self._repo = repo

    async def ejecutar(
        self, usuario: Usuario, datos: SolicitudOrganizadorRequest
    ) -> Organizador:
        existente = await self._repo.get_by_usuario_id(usuario.id)

        if existente is None:
            # Estado explicito y no solo el default de la columna: que la
            # solicitud nace PENDIENTE es una regla de este caso de uso.
            return await self._repo.add(
                Organizador(
                    id_usuario=usuario.id,
                    nombre_publico=datos.nombre_publico,
                    descripcion=datos.descripcion,
                    estado=EstadoOrganizador.PENDIENTE,
                )
            )

        if existente.estado == EstadoOrganizador.SUSPENDIDO:
            raise OrganizadorSuspendidoError()
        if existente.estado != EstadoOrganizador.RECHAZADO:
            raise SolicitudYaExistenteError(existente.estado)

        # Un rechazado puede volver a solicitar (CU-04, 5a): se reutiliza la
        # misma fila porque id_usuario es UNIQUE (multiplicidad 0..1).
        existente.reenviar_solicitud(datos.nombre_publico, datos.descripcion)
        return existente


class ListarSolicitudesOrganizador:
    """Un administrador lista los perfiles de organizador en un estado dado,
    tipicamente PENDIENTE para revisar las solicitudes del CU-04."""

    def __init__(self, repo: OrganizadorRepository) -> None:
        self._repo = repo

    async def ejecutar(self, estado: EstadoOrganizador) -> list[Organizador]:
        return await self._repo.list_by_estado(estado)


class AprobarOrganizador:
    """CU-05: un administrador aprueba una solicitud PENDIENTE."""

    def __init__(self, repo: OrganizadorRepository) -> None:
        self._repo = repo

    async def ejecutar(self, id_organizador: UUID) -> Organizador:
        organizador = await self._repo.get_by_id(id_organizador)
        if organizador is None:
            raise OrganizadorNoEncontradoError()
        organizador.aprobar()
        return organizador


class RechazarOrganizador:
    """CU-05: un administrador rechaza una solicitud PENDIENTE."""

    def __init__(self, repo: OrganizadorRepository) -> None:
        self._repo = repo

    async def ejecutar(self, id_organizador: UUID) -> Organizador:
        organizador = await self._repo.get_by_id(id_organizador)
        if organizador is None:
            raise OrganizadorNoEncontradoError()
        organizador.rechazar()
        return organizador


class SuspenderOrganizador:
    """CU-05: un administrador suspende un perfil APROBADO."""

    def __init__(self, repo: OrganizadorRepository) -> None:
        self._repo = repo

    async def ejecutar(self, id_organizador: UUID) -> Organizador:
        organizador = await self._repo.get_by_id(id_organizador)
        if organizador is None:
            raise OrganizadorNoEncontradoError()
        organizador.suspender()
        return organizador
