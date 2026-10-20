from uuid import uuid4

import pytest

from app.organizadores.models import EstadoOrganizador, Organizador
from app.organizadores.service import ListarSolicitudesOrganizador
from tests.organizadores.test_solicitar_organizador import (
    InMemoryOrganizadorRepository,
)


@pytest.fixture
def repo() -> InMemoryOrganizadorRepository:
    return InMemoryOrganizadorRepository()


async def _perfil(repo, estado: EstadoOrganizador) -> Organizador:
    return await repo.add(
        Organizador(
            id_usuario=uuid4(),
            nombre_publico='Bar Los Pinos',
            descripcion='Musica en vivo',
            estado=estado,
        )
    )


async def test_devuelve_solo_los_del_estado_pedido(repo):
    pendiente = await _perfil(repo, EstadoOrganizador.PENDIENTE)
    await _perfil(repo, EstadoOrganizador.APROBADO)
    await _perfil(repo, EstadoOrganizador.RECHAZADO)

    resultado = await ListarSolicitudesOrganizador(repo).ejecutar(
        EstadoOrganizador.PENDIENTE
    )

    assert resultado == [pendiente]


async def test_sin_coincidencias_devuelve_lista_vacia(repo):
    await _perfil(repo, EstadoOrganizador.APROBADO)

    resultado = await ListarSolicitudesOrganizador(repo).ejecutar(
        EstadoOrganizador.PENDIENTE
    )

    assert resultado == []
