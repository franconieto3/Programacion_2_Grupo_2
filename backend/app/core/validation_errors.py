"""Traduce al espanol los errores de validacion de Pydantic (422).

FastAPI responde los 422 con mensajes en ingles ("Field required",
"value is not a valid email address"...). Este handler conserva el mismo
formato, {"detail": [{"loc", "msg", "type"}]}, para que el frontend siga
ubicando cada error en su campo por `loc`, y solo cambia `msg`.

No devuelve `input` ni `ctx`: `input` repetiria lo enviado (por ejemplo,
la contrasena) y `ctx` puede traer objetos que no son JSON."""

from collections.abc import Callable
from decimal import Decimal
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

_PREFIJO_EMAIL = 'value is not a valid email address'
_PREFIJO_VALIDADOR_PROPIO = 'Value error, '

_FECHA_HORA = 'Ingresá una fecha y hora válidas.'
_FECHA = 'Ingresá una fecha válida.'
_HORARIO = 'Ingresá un horario válido (HH:MM).'
_NUMERO = 'Ingresá un número válido.'
_ENTERO = 'Ingresá un número entero.'


def _numero(valor: Any) -> str:
    """90.0 -> '90', Decimal('0') -> '0', 0.5 -> '0.5'."""
    if isinstance(valor, (float, Decimal)) and valor == int(valor):
        return str(int(valor))
    return str(valor)


def _texto_corto(ctx: dict) -> str:
    if ctx['min_length'] == 1:
        return 'Este campo es obligatorio.'
    return f'Tiene que tener al menos {ctx["min_length"]} caracteres.'


def _lista_corta(ctx: dict) -> str:
    if ctx['min_length'] == 1:
        return 'Elegí al menos una opción.'
    return f'Elegí al menos {ctx["min_length"]} opciones.'


def _opciones(ctx: dict) -> str:
    return f'Tiene que ser uno de: {ctx["expected"].replace(" or ", " o ")}.'


_MENSAJES: dict[str, Callable[[dict], str]] = {
    'missing': lambda _: 'Este campo es obligatorio.',
    'string_too_short': _texto_corto,
    'string_too_long': lambda ctx: (
        f'Puede tener como máximo {ctx["max_length"]} caracteres.'
    ),
    'string_type': lambda _: 'Tiene que ser un texto.',
    'too_short': _lista_corta,
    'too_long': lambda ctx: (
        f'Podés elegir como máximo {ctx["max_length"]} opciones.'
    ),
    'list_type': lambda _: 'Tiene que ser una lista.',
    'greater_than_equal': lambda ctx: (
        f'Tiene que ser mayor o igual a {_numero(ctx["ge"])}.'
    ),
    'greater_than': lambda ctx: f'Tiene que ser mayor a {_numero(ctx["gt"])}.',
    'less_than_equal': lambda ctx: (
        f'Tiene que ser menor o igual a {_numero(ctx["le"])}.'
    ),
    'less_than': lambda ctx: f'Tiene que ser menor a {_numero(ctx["lt"])}.',
    'timezone_aware': lambda _: 'La fecha tiene que incluir la zona horaria.',
    'datetime_parsing': lambda _: _FECHA_HORA,
    'datetime_from_date_parsing': lambda _: _FECHA_HORA,
    'datetime_type': lambda _: _FECHA_HORA,
    'date_parsing': lambda _: _FECHA,
    'date_from_datetime_parsing': lambda _: _FECHA,
    'date_type': lambda _: _FECHA,
    'time_parsing': lambda _: _HORARIO,
    'time_type': lambda _: _HORARIO,
    'float_parsing': lambda _: _NUMERO,
    'float_type': lambda _: _NUMERO,
    'decimal_parsing': lambda _: _NUMERO,
    'decimal_type': lambda _: _NUMERO,
    'int_parsing': lambda _: _ENTERO,
    'int_type': lambda _: _ENTERO,
    'int_from_float': lambda _: _ENTERO,
    'decimal_max_digits': lambda ctx: (
        f'Puede tener como máximo {ctx["max_digits"]} dígitos.'
    ),
    'decimal_max_places': lambda ctx: (
        f'Puede tener como máximo {ctx["decimal_places"]} decimales.'
    ),
    'bool_parsing': lambda _: 'Tiene que ser verdadero o falso.',
    'bool_type': lambda _: 'Tiene que ser verdadero o falso.',
    'uuid_parsing': lambda _: 'El identificador no es válido.',
    'uuid_type': lambda _: 'El identificador no es válido.',
    'enum': _opciones,
    'literal_error': _opciones,
    'extra_forbidden': lambda _: 'Este campo no está permitido.',
    'model_attributes_type': lambda _: 'El formato de los datos no es válido.',
    'dict_type': lambda _: 'El formato de los datos no es válido.',
    'json_invalid': lambda _: (
        'El cuerpo de la solicitud no es un JSON válido.'
    ),
}


def traducir_error(error: dict) -> str:
    """Mensaje en espanol para un error de `ValidationError.errors()`.

    Los validadores propios (model_validator que lanzan ValueError) ya
    escriben en espanol: solo se les quita el prefijo "Value error, " que
    agrega Pydantic. Un tipo que no esta en la tabla conserva el mensaje
    original, asi nunca se pierde la informacion del error."""
    tipo = error.get('type')
    msg = error.get('msg', '')
    if tipo == 'value_error':
        if msg.startswith(_PREFIJO_EMAIL):
            return 'El email no es válido.'
        return msg.removeprefix(_PREFIJO_VALIDADOR_PROPIO)

    traductor = _MENSAJES.get(tipo)
    if traductor is None:
        return msg
    try:
        return traductor(error.get('ctx') or {})
    except (KeyError, TypeError, ValueError):
        # ctx distinto del esperado (otra version de Pydantic): mejor el
        # mensaje original que un 500.
        return msg


def _validation_handler(
    _request: Request, exc: RequestValidationError
) -> JSONResponse:
    detalle = [
        {
            'loc': list(error['loc']),
            'msg': traducir_error(error),
            'type': error['type'],
        }
        for error in exc.errors()
    ]
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={'detail': detalle},
    )


def register_validation_exception_handler(app: FastAPI) -> None:
    app.add_exception_handler(RequestValidationError, _validation_handler)
