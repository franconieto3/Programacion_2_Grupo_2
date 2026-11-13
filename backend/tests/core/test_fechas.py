from datetime import datetime, timedelta, timezone

from app.core.fechas import como_utc


def test_fecha_sin_zona_se_interpreta_como_utc():
    assert como_utc(datetime(2026, 11, 21, 0, 30)) == datetime(
        2026, 11, 21, 0, 30, tzinfo=timezone.utc
    )


def test_fecha_con_zona_no_cambia():
    menos_tres = timezone(timedelta(hours=-3))
    fecha = datetime(2026, 11, 20, 21, 30, tzinfo=menos_tres)

    assert como_utc(fecha) is fecha
