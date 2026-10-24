"""Composition root del modulo de eventos: el unico lugar que conoce la
implementacion concreta del repositorio. Los servicios solo ven el Protocol
EventoRepository."""

from zoneinfo import ZoneInfo

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.categorias.dependencies import get_categoria_repository
from app.categorias.repository import CategoriaRepository
from app.core.config import Settings, get_settings
from app.db.session import get_db_session
from app.eventos.factory import EventoFactory
from app.eventos.repository import (
    EventoRepository,
    SQLAlchemyEventoRepository,
)
from app.eventos.service import (
    BuscarEventos,
    CancelarEvento,
    EditarEvento,
    ListarMisEventos,
    OcultarEvento,
)


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


def get_listar_mis_eventos(
    repo: EventoRepository = Depends(get_evento_repository),
) -> ListarMisEventos:
    return ListarMisEventos(repo)


def get_editar_evento(
    repo: EventoRepository = Depends(get_evento_repository),
    categorias: CategoriaRepository = Depends(get_categoria_repository),
    settings: Settings = Depends(get_settings),
) -> EditarEvento:
    return EditarEvento(repo, categorias, ZoneInfo(settings.zona_horaria))


def get_cancelar_evento(
    repo: EventoRepository = Depends(get_evento_repository),
) -> CancelarEvento:
    return CancelarEvento(repo)


def get_ocultar_evento(
    repo: EventoRepository = Depends(get_evento_repository),
) -> OcultarEvento:
    return OcultarEvento(repo)
