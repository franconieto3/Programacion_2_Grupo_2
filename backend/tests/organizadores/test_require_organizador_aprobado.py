"""RF-01.7: solo un organizador APROBADO puede gestionar eventos."""

from uuid import uuid4

import pytest

from app.models.usuario import Usuario
from app.organizadores.dependencies import require_organizador_aprobado
from app.organizadores.exceptions import OrganizadorNoAprobadoError
from app.organizadores.models import EstadoOrganizador, Organizador
from tests.organizadores.test_solicitar_organizador import (
    InMemoryOrganizadorRepository,
)


def _usuario() -> Usuario:
    return Usuario(id=uuid4(), nombre='Ana', apellido='Gomez', email='a@a.com')


async def _con_perfil(repo, usuario, estado) -> Organizador:
    return await repo.add(
        Organizador(
            id_organizador=uuid4(),
            id_usuario=usuario.id,
            nombre_publico='Bar Los Pinos',
            descripcion='Musica en vivo',
            estado=estado,
        )
    )


async def test_organizador_aprobado_devuelve_su_perfil():
    repo = InMemoryOrganizadorRepository()
    usuario = _usuario()
    perfil = await _con_perfil(repo, usuario, EstadoOrganizador.APROBADO)

    assert await require_organizador_aprobado(usuario, repo) is perfil


async def test_sin_perfil_de_organizador_falla():
    with pytest.raises(OrganizadorNoAprobadoError):
        await require_organizador_aprobado(
            _usuario(), InMemoryOrganizadorRepository()
        )


@pytest.mark.parametrize(
    'estado',
    [
        EstadoOrganizador.PENDIENTE,
        EstadoOrganizador.RECHAZADO,
        EstadoOrganizador.SUSPENDIDO,
    ],
)
async def test_perfil_no_aprobado_falla(estado):
    repo = InMemoryOrganizadorRepository()
    usuario = _usuario()
    await _con_perfil(repo, usuario, estado)

    with pytest.raises(OrganizadorNoAprobadoError):
        await require_organizador_aprobado(usuario, repo)
