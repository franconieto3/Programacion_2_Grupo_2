"""Composition root del modulo de eventos: el unico lugar que conoce la
implementacion concreta del repositorio. Los servicios solo ven el Protocol
EventoRepository."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
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
