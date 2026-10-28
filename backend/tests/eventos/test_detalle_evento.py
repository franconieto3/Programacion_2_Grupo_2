"""Caso de uso de la ficha de detalle (RF-03.10), con repositorios en
memoria. La regla de visibilidad por estado se prueba en
test_evento_model.py; aca, que el servicio la aplique con el perfil
correcto y resuelva el organizador."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.eventos.exceptions import EventoNoEncontradoError
from app.eventos.models import EstadoEvento
from app.eventos.service import ObtenerDetalleEvento
from app.models.usuario import Usuario
from tests.eventos.test_gestion_eventos import (
    InMemoryEventoRepository,
    evento,
    organizador,
)
from tests.organizadores.test_solicitar_organizador import (
    InMemoryOrganizadorRepository,
)


def _usuario() -> Usuario:
    return Usuario(
        id=uuid4(),
        email=f'{uuid4()}@a.com',
        password_hash='x',
        nombre='Ana',
        apellido='Gomez',
        activo=True,
        creado_en=datetime.now(timezone.utc),
    )


@pytest.fixture
def eventos() -> InMemoryEventoRepository:
    return InMemoryEventoRepository()


@pytest.fixture
def organizadores() -> InMemoryOrganizadorRepository:
    return InMemoryOrganizadorRepository()


@pytest.fixture
def servicio(eventos, organizadores) -> ObtenerDetalleEvento:
    return ObtenerDetalleEvento(eventos, organizadores)


async def _duenio(organizadores, usuario: Usuario):
    perfil = organizador()
    perfil.id_usuario = usuario.id
    return await organizadores.add(perfil)


async def test_publicado_devuelve_evento_y_organizador(
    servicio, eventos, organizadores
):
    perfil = await _duenio(organizadores, _usuario())
    original = await eventos.add(evento(perfil))

    encontrado, su_organizador = await servicio.ejecutar(
        _usuario(), original.id_evento
    )

    assert encontrado is original
    assert su_organizador is perfil


async def test_seed_no_tiene_organizador(servicio, eventos):
    original = await eventos.add(evento(None))

    encontrado, su_organizador = await servicio.ejecutar(
        _usuario(), original.id_evento
    )

    assert encontrado is original
    assert su_organizador is None


async def test_cancelado_sigue_visible(servicio, eventos):
    original = await eventos.add(evento(None, estado=EstadoEvento.CANCELADO))

    encontrado, _ = await servicio.ejecutar(_usuario(), original.id_evento)

    assert encontrado is original


async def test_oculto_no_se_encuentra_ni_para_su_duenio(
    servicio, eventos, organizadores
):
    usuario = _usuario()
    perfil = await _duenio(organizadores, usuario)
    original = await eventos.add(evento(perfil, estado=EstadoEvento.OCULTO))

    with pytest.raises(EventoNoEncontradoError):
        await servicio.ejecutar(usuario, original.id_evento)


async def test_borrador_lo_ve_su_duenio(servicio, eventos, organizadores):
    usuario = _usuario()
    perfil = await _duenio(organizadores, usuario)
    original = await eventos.add(evento(perfil, estado=EstadoEvento.BORRADOR))

    encontrado, su_organizador = await servicio.ejecutar(
        usuario, original.id_evento
    )

    assert encontrado is original
    assert su_organizador is perfil


async def test_borrador_ajeno_no_se_encuentra(
    servicio, eventos, organizadores
):
    perfil = await _duenio(organizadores, _usuario())
    otro = _usuario()
    await _duenio(organizadores, otro)
    original = await eventos.add(evento(perfil, estado=EstadoEvento.BORRADOR))

    with pytest.raises(EventoNoEncontradoError):
        await servicio.ejecutar(otro, original.id_evento)


async def test_borrador_no_se_encuentra_sin_perfil_de_organizador(
    servicio, eventos, organizadores
):
    perfil = await _duenio(organizadores, _usuario())
    original = await eventos.add(evento(perfil, estado=EstadoEvento.BORRADOR))

    with pytest.raises(EventoNoEncontradoError):
        await servicio.ejecutar(_usuario(), original.id_evento)


async def test_id_inexistente_no_se_encuentra(servicio):
    with pytest.raises(EventoNoEncontradoError):
        await servicio.ejecutar(_usuario(), uuid4())
