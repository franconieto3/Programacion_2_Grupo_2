from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import Select

from app.core.config import get_settings
from app.eventos.models import Evento
from app.eventos.schemas import BusquedaEventosParams


def filtrar_por_fechas(
    consulta: Select, filtros: BusquedaEventosParams
) -> Select:
    """Filtro por rango de fechas (desde, hasta) (RF-03.4).

    `desde` y `hasta` son fechas locales (Settings.zona_horaria) y
    `fecha_inicio` esta en UTC, asi que cada limite se convierte a UTC.
    Ambos extremos son inclusivos: `desde` arranca a las 00:00 locales de
    ese dia y `hasta` llega hasta el fin de su dia (se compara contra las
    00:00 locales del dia siguiente, excluyente). Se filtra por el inicio
    del evento. Sin `desde` ni `hasta` no filtra; con uno solo, el otro
    extremo queda abierto."""
    if filtros.desde is None and filtros.hasta is None:
        return consulta

    zona = ZoneInfo(get_settings().zona_horaria)
    if filtros.desde is not None:
        consulta = consulta.where(
            Evento.fecha_inicio >= _inicio_del_dia_utc(filtros.desde, zona)
        )
    if filtros.hasta is not None:
        dia_siguiente = filtros.hasta + timedelta(days=1)
        consulta = consulta.where(
            Evento.fecha_inicio < _inicio_del_dia_utc(dia_siguiente, zona)
        )
    return consulta


def _inicio_del_dia_utc(dia: date, zona: ZoneInfo) -> datetime:
    """Las 00:00 de `dia` en `zona`, expresadas en UTC."""
    return datetime.combine(dia, time.min, tzinfo=zona).astimezone(
        timezone.utc
    )
