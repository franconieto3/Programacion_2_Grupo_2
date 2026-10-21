from datetime import datetime, time, timezone
from zoneinfo import ZoneInfo

import pytest

from app.eventos.exceptions import TransicionEstadoEventoInvalidaError
from app.eventos.models import EstadoEvento, Evento

BUENOS_AIRES = ZoneInfo('America/Argentina/Buenos_Aires')


def test_programar_calcula_la_hora_local_de_inicio():
    evento = Evento()
    # 00:30 UTC del 21/11 son las 21:30 del 20/11 en Buenos Aires (UTC-3).
    inicio = datetime(2026, 11, 21, 0, 30, tzinfo=timezone.utc)

    evento.programar(inicio, None, BUENOS_AIRES)

    assert evento.fecha_inicio == inicio
    assert evento.fecha_fin is None
    assert evento.hora_inicio_local == time(21, 30)


@pytest.mark.parametrize(
    'estado_origen', [EstadoEvento.BORRADOR, EstadoEvento.PUBLICADO]
)
def test_cancelar_desde_estado_valido(estado_origen):
    evento = Evento(estado=estado_origen)

    evento.cancelar()

    assert evento.estado == EstadoEvento.CANCELADO


@pytest.mark.parametrize(
    'estado_origen', [EstadoEvento.CANCELADO, EstadoEvento.OCULTO]
)
def test_cancelar_desde_estado_invalido_lanza_error(estado_origen):
    evento = Evento(estado=estado_origen)

    with pytest.raises(TransicionEstadoEventoInvalidaError):
        evento.cancelar()

    assert evento.estado == estado_origen


@pytest.mark.parametrize(
    'estado_origen', [EstadoEvento.PUBLICADO, EstadoEvento.CANCELADO]
)
def test_ocultar_desde_estado_valido(estado_origen):
    evento = Evento(estado=estado_origen)

    evento.ocultar()

    assert evento.estado == EstadoEvento.OCULTO


@pytest.mark.parametrize(
    'estado_origen', [EstadoEvento.BORRADOR, EstadoEvento.OCULTO]
)
def test_ocultar_desde_estado_invalido_lanza_error(estado_origen):
    evento = Evento(estado=estado_origen)

    with pytest.raises(TransicionEstadoEventoInvalidaError):
        evento.ocultar()

    assert evento.estado == estado_origen
