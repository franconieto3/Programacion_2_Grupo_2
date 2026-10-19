"""Composition root del modulo de organizadores: el unico lugar que conoce
la implementacion concreta del repositorio. Los servicios solo ven el
Protocol OrganizadorRepository."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.organizadores.repository import (
    OrganizadorRepository,
    SQLAlchemyOrganizadorRepository,
)
from app.organizadores.service import SolicitarOrganizador


def get_organizador_repository(
    session: AsyncSession = Depends(get_db_session),
) -> OrganizadorRepository:
    return SQLAlchemyOrganizadorRepository(session)


def get_solicitar_organizador(
    repo: OrganizadorRepository = Depends(get_organizador_repository),
) -> SolicitarOrganizador:
    return SolicitarOrganizador(repo)
