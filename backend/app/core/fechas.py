from datetime import datetime, timezone


def como_utc(fecha: datetime) -> datetime:
    """Las fechas se guardan siempre en UTC (DateTime(timezone=True)). En
    PostgreSQL vuelven con zona horaria, pero SQLite (tests y pruebas
    locales, RNF-05.2) no la guarda y las devuelve sin ella. Compararlas con
    una fecha con zona lanza TypeError, y astimezone() las tomaria como hora
    local del sistema. Una fecha sin zona horaria se interpreta como UTC."""
    if fecha.tzinfo is None:
        return fecha.replace(tzinfo=timezone.utc)
    return fecha
