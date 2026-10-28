"""Un .env con una ubicacion por defecto imposible tiene que hacer fallar
el arranque (Settings no se construye), no centrar el mapa en cualquier
lado."""

import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_por_defecto_es_buenos_aires():
    settings = Settings(_env_file=None)

    assert settings.ubicacion_default_nombre == 'Buenos Aires'
    assert settings.ubicacion_default_lat == pytest.approx(-34.6037)
    assert settings.ubicacion_default_lng == pytest.approx(-58.3816)
    assert settings.ubicacion_default_zoom == 12


@pytest.mark.parametrize(
    'valores',
    [
        {'ubicacion_default_lat': 91},
        {'ubicacion_default_lat': -91},
        {'ubicacion_default_lng': 181},
        {'ubicacion_default_lng': -181},
        {'ubicacion_default_zoom': -1},
        {'ubicacion_default_zoom': 20},
    ],
)
def test_valores_fuera_de_rango_se_rechazan(valores):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **valores)


def test_se_lee_de_variables_de_entorno(monkeypatch):
    monkeypatch.setenv('UBICACION_DEFAULT_LAT', '-31.42')
    monkeypatch.setenv('UBICACION_DEFAULT_ZOOM', '10')

    settings = Settings(_env_file=None)

    assert settings.ubicacion_default_lat == pytest.approx(-31.42)
    assert settings.ubicacion_default_zoom == 10
