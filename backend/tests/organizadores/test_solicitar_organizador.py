from uuid import UUID, uuid4

import pytest

from app.models.usuario import Usuario
from app.organizadores.exceptions import (
    OrganizadorSuspendidoError,
    SolicitudYaExistenteError,
)
from app.organizadores.models import EstadoOrganizador, Organizador
from app.organizadores.schemas import SolicitudOrganizadorRequest
from app.organizadores.service import SolicitarOrganizador


class InMemoryOrganizadorRepository:
    def __init__(self) -> None:
        self._by_usuario_id: dict[UUID, Organizador] = {}

    async def get_by_usuario_id(self, usuario_id: UUID) -> Organizador | None:
        return self._by_usuario_id.get(usuario_id)

    async def add(self, organizador: Organizador) -> Organizador:
        self._by_usuario_id[organizador.id_usuario] = organizador
        return organizador


@pytest.fixture
def repo() -> InMemoryOrganizadorRepository:
    return InMemoryOrganizadorRepository()


@pytest.fixture
def usuario() -> Usuario:
    return Usuario(id=uuid4(), nombre='Ana', apellido='Gomez', email='a@a.com')


def _datos(
    nombre_publico: str = 'Bar Los Pinos',
) -> SolicitudOrganizadorRequest:
    return SolicitudOrganizadorRequest(
        nombre_publico=nombre_publico, descripcion='Musica en vivo'
    )


async def _perfil_existente(repo, usuario, estado) -> Organizador:
    return await repo.add(
        Organizador(
            id_usuario=usuario.id,
            nombre_publico='Nombre anterior',
            descripcion='Descripcion anterior',
            estado=estado,
        )
    )


async def test_sin_perfil_crea_solicitud_pendiente(repo, usuario):
    resultado = await SolicitarOrganizador(repo).ejecutar(usuario, _datos())

    assert resultado.id_usuario == usuario.id
    assert resultado.nombre_publico == 'Bar Los Pinos'
    assert resultado.estado == EstadoOrganizador.PENDIENTE
    assert await repo.get_by_usuario_id(usuario.id) is resultado


@pytest.mark.parametrize(
    'estado', [EstadoOrganizador.PENDIENTE, EstadoOrganizador.APROBADO]
)
async def test_con_perfil_pendiente_o_aprobado_rechaza(repo, usuario, estado):
    await _perfil_existente(repo, usuario, estado)

    with pytest.raises(SolicitudYaExistenteError):
        await SolicitarOrganizador(repo).ejecutar(usuario, _datos())


async def test_con_perfil_suspendido_rechaza(repo, usuario):
    await _perfil_existente(repo, usuario, EstadoOrganizador.SUSPENDIDO)

    with pytest.raises(OrganizadorSuspendidoError):
        await SolicitarOrganizador(repo).ejecutar(usuario, _datos())


async def test_con_perfil_rechazado_reenvia_la_solicitud(repo, usuario):
    anterior = await _perfil_existente(
        repo, usuario, EstadoOrganizador.RECHAZADO
    )

    resultado = await SolicitarOrganizador(repo).ejecutar(
        usuario, _datos('Nombre nuevo')
    )

    assert resultado is anterior
    assert resultado.estado == EstadoOrganizador.PENDIENTE
    assert resultado.nombre_publico == 'Nombre nuevo'
    assert resultado.descripcion == 'Musica en vivo'
