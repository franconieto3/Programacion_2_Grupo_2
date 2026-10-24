"""Composition root del modulo de eventos: el unico lugar que conoce la
implementacion concreta del repositorio. Los servicios solo ven el Protocol
EventoRepository."""

from zoneinfo import ZoneInfo

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.session import get_db_session
from app.eventos.factory import EventoFactory
from app.eventos.repository import (
    EventoRepository,
    SQLAlchemyEventoRepository,
)
from app.eventos.service import BuscarEventos


def get_evento_repository(
    session: AsyncSession = Depends(get_db_session),
) -> EventoRepository:
    return SQLAlchemyEventoRepository(session)


def get_buscar_eventos(
    repo: EventoRepository = Depends(get_evento_repository),
) -> BuscarEventos:
    return BuscarEventos(repo)


def get_evento_factory(
    settings: Settings = Depends(get_settings),
) -> EventoFactory:
    return EventoFactory(ZoneInfo(settings.zona_horaria))
