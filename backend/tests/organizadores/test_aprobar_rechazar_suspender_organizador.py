from uuid import uuid4

import pytest

from app.organizadores.exceptions import (
    OrganizadorNoEncontradoError,
    TransicionEstadoInvalidaError,
)
from app.organizadores.models import EstadoOrganizador, Organizador
from app.organizadores.service import (
    AprobarOrganizador,
    RechazarOrganizador,
    SuspenderOrganizador,
)
from tests.organizadores.test_solicitar_organizador import (
    InMemoryOrganizadorRepository,
)


@pytest.fixture
def repo() -> InMemoryOrganizadorRepository:
    return InMemoryOrganizadorRepository()


async def _perfil(repo, estado: EstadoOrganizador) -> Organizador:
    return await repo.add(
        Organizador(
            id_organizador=uuid4(),
            id_usuario=uuid4(),
            nombre_publico='Bar Los Pinos',
            descripcion='Musica en vivo',
            estado=estado,
        )
    )


async def test_aprobar_desde_pendiente_cambia_el_estado(repo):
    organizador = await _perfil(repo, EstadoOrganizador.PENDIENTE)

    resultado = await AprobarOrganizador(repo).ejecutar(
        organizador.id_organizador
    )

    assert resultado is organizador
    assert resultado.estado == EstadoOrganizador.APROBADO


@pytest.mark.parametrize(
    'estado',
    [
        EstadoOrganizador.APROBADO,
        EstadoOrganizador.RECHAZADO,
        EstadoOrganizador.SUSPENDIDO,
    ],
)
async def test_aprobar_desde_estado_invalido_lanza_transicion_invalida(
    repo, estado
):
    organizador = await _perfil(repo, estado)

    with pytest.raises(TransicionEstadoInvalidaError):
        await AprobarOrganizador(repo).ejecutar(organizador.id_organizador)


async def test_aprobar_id_inexistente_lanza_no_encontrado(repo):
    with pytest.raises(OrganizadorNoEncontradoError):
        await AprobarOrganizador(repo).ejecutar(uuid4())


async def test_rechazar_desde_pendiente_cambia_el_estado(repo):
    organizador = await _perfil(repo, EstadoOrganizador.PENDIENTE)

    resultado = await RechazarOrganizador(repo).ejecutar(
        organizador.id_organizador
    )

    assert resultado is organizador
    assert resultado.estado == EstadoOrganizador.RECHAZADO


@pytest.mark.parametrize(
    'estado',
    [
        EstadoOrganizador.APROBADO,
        EstadoOrganizador.RECHAZADO,
        EstadoOrganizador.SUSPENDIDO,
    ],
)
async def test_rechazar_desde_estado_invalido_lanza_transicion_invalida(
    repo, estado
):
    organizador = await _perfil(repo, estado)

    with pytest.raises(TransicionEstadoInvalidaError):
        await RechazarOrganizador(repo).ejecutar(organizador.id_organizador)


async def test_rechazar_id_inexistente_lanza_no_encontrado(repo):
    with pytest.raises(OrganizadorNoEncontradoError):
        await RechazarOrganizador(repo).ejecutar(uuid4())


async def test_suspender_desde_aprobado_cambia_el_estado(repo):
    organizador = await _perfil(repo, EstadoOrganizador.APROBADO)

    resultado = await SuspenderOrganizador(repo).ejecutar(
        organizador.id_organizador
    )

    assert resultado is organizador
    assert resultado.estado == EstadoOrganizador.SUSPENDIDO


@pytest.mark.parametrize(
    'estado',
    [
        EstadoOrganizador.PENDIENTE,
        EstadoOrganizador.RECHAZADO,
        EstadoOrganizador.SUSPENDIDO,
    ],
)
async def test_suspender_desde_estado_invalido_lanza_transicion_invalida(
    repo, estado
):
    organizador = await _perfil(repo, estado)

    with pytest.raises(TransicionEstadoInvalidaError):
        await SuspenderOrganizador(repo).ejecutar(organizador.id_organizador)


async def test_suspender_id_inexistente_lanza_no_encontrado(repo):
    with pytest.raises(OrganizadorNoEncontradoError):
        await SuspenderOrganizador(repo).ejecutar(uuid4())
