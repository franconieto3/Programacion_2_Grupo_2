"""Traduccion de los errores de validacion de Pydantic (B-3). Los unitarios
validan modelos reales del proyecto, asi el `type` y el `ctx` son los que
produce la version instalada de Pydantic y no una copia escrita a mano."""

from decimal import Decimal

import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError

from app.auth.dependencies import (
    get_auth_event_publisher,
    get_reset_token_repository,
    get_token_service,
    get_user_repository,
)
from app.auth.events.publisher import AuthEventPublisher
from app.auth.schemas import RegisterRequest
from app.core.validation_errors import traducir_error
from app.eventos.schemas import (
    BusquedaEventosParams,
    CrearEventoRequest,
    EditarEventoRequest,
)
from app.main import app
from tests.conftest import (
    FakeTokenService,
    InMemoryResetTokenRepository,
    InMemoryUserRepository,
)

_REGISTRO_VALIDO = {
    'email': 'a@a.com',
    'password': 'secret123',
    'nombre': 'Ana',
    'apellido': 'Gomez',
}
_EVENTO_VALIDO = {
    'titulo': 'Recital',
    'descripcion': 'En vivo',
    'fecha_inicio': '2026-12-01T21:00:00Z',
    'lugar': {'latitud': -34.6, 'longitud': -58.4},
    'categorias': ['musica'],
}


def _mensajes(modelo, datos) -> dict[tuple, str]:
    with pytest.raises(ValidationError) as info:
        modelo.model_validate(datos)
    return {e['loc']: traducir_error(e) for e in info.value.errors()}


def test_registro():
    mensajes = _mensajes(
        RegisterRequest,
        {
            'email': 'sin-arroba',
            'password': '123',
            'nombre': '',
            'apellido': 'a' * 300,
        },
    )
    assert mensajes == {
        ('email',): 'El email no es válido.',
        ('password',): 'Tiene que tener al menos 8 caracteres.',
        ('nombre',): 'Este campo es obligatorio.',
        ('apellido',): 'Puede tener como máximo 255 caracteres.',
    }


def test_campos_faltantes():
    mensajes = _mensajes(RegisterRequest, {})
    assert set(mensajes.values()) == {'Este campo es obligatorio.'}


def test_evento_numeros_fechas_y_listas():
    mensajes = _mensajes(
        CrearEventoRequest,
        {
            **_EVENTO_VALIDO,
            'fecha_inicio': '2026-12-01T21:00',
            'precio': '-1',
            'lugar': {'latitud': 100, 'longitud': 'x'},
            'categorias': [],
            'extra': 1,
        },
    )
    assert mensajes == {
        ('fecha_inicio',): 'La fecha tiene que incluir la zona horaria.',
        ('precio',): 'Tiene que ser mayor o igual a 0.',
        ('lugar', 'latitud'): 'Tiene que ser menor o igual a 90.',
        ('lugar', 'longitud'): 'Ingresá un número válido.',
        ('categorias',): 'Elegí al menos una opción.',
        ('extra',): 'Este campo no está permitido.',
    }


def test_evento_precio_con_demasiados_decimales_y_fecha_invalida():
    mensajes = _mensajes(
        CrearEventoRequest,
        {**_EVENTO_VALIDO, 'fecha_inicio': 'hola', 'precio': Decimal('1.234')},
    )
    assert mensajes == {
        ('fecha_inicio',): 'Ingresá una fecha y hora válidas.',
        ('precio',): 'Puede tener como máximo 2 decimales.',
    }


def test_busqueda_fecha_horario_y_entero():
    mensajes = _mensajes(
        BusquedaEventosParams,
        {'desde': 'x', 'hora_desde': '25:00', 'limit': 'abc'},
    )
    assert mensajes == {
        ('desde',): 'Ingresá una fecha válida.',
        ('hora_desde',): 'Ingresá un horario válido (HH:MM).',
        ('limit',): 'Ingresá un número entero.',
    }


def test_validador_propio_conserva_su_mensaje_sin_prefijo():
    mensajes = _mensajes(EditarEventoRequest, {'titulo': None})
    assert mensajes == {(): 'No pueden ser null: titulo.'}


def test_tipo_desconocido_conserva_el_mensaje_original():
    error = {'type': 'tipo_nuevo', 'loc': ('x',), 'msg': 'Original'}
    assert traducir_error(error) == 'Original'


def test_ctx_inesperado_conserva_el_mensaje_original():
    error = {'type': 'string_too_short', 'loc': ('x',), 'msg': 'Original'}
    assert traducir_error(error) == 'Original'


@pytest.fixture
def wired_app():
    app.dependency_overrides[get_user_repository] = InMemoryUserRepository
    app.dependency_overrides[get_token_service] = FakeTokenService
    app.dependency_overrides[get_reset_token_repository] = (
        InMemoryResetTokenRepository
    )
    app.dependency_overrides[get_auth_event_publisher] = AuthEventPublisher
    yield
    app.dependency_overrides.clear()


async def test_respuesta_http_en_espanol_con_el_formato_de_fastapi(wired_app):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url='http://test'
    ) as client:
        response = await client.post(
            '/auth/register',
            json={**_REGISTRO_VALIDO, 'email': 'x', 'password': 'corta'},
        )

    assert response.status_code == 422
    assert response.json() == {
        'detail': [
            {
                'loc': ['body', 'email'],
                'msg': 'El email no es válido.',
                'type': 'value_error',
            },
            {
                'loc': ['body', 'password'],
                'msg': 'Tiene que tener al menos 8 caracteres.',
                'type': 'string_too_short',
            },
        ]
    }
    # No se refleja lo enviado (la contrasena) en la respuesta.
    assert 'corta' not in response.text
