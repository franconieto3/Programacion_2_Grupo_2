"""tabla organizadores (perfil de organizador, CU-04)

Revision ID: 0002_organizadores
Revises: 0001_auth_tables
Create Date: 2026-10-19

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_organizadores"
down_revision: Union[str, None] = "0001_auth_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_estado_organizador = sa.Enum(
    "PENDIENTE", "APROBADO", "RECHAZADO", "SUSPENDIDO", name="estado_organizador"
)


def _uuid_type():
    return sa.String(36).with_variant(postgresql.UUID(as_uuid=True), "postgresql")


def upgrade() -> None:
    op.create_table(
        "organizadores",
        sa.Column("id_organizador", _uuid_type(), primary_key=True),
        # UNIQUE: un solo perfil por usuario (multiplicidad 0..1). En
        # PostgreSQL la restriccion ya crea el indice para buscar por usuario.
        sa.Column(
            "id_usuario",
            _uuid_type(),
            sa.ForeignKey("usuario.id_usuario", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("nombre_publico", sa.String(255), nullable=False),
        sa.Column("descripcion", sa.Text, nullable=False),
        sa.Column("estado", _estado_organizador, nullable=False),
        sa.Column(
            "fecha_creacion",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    op.drop_table("organizadores")
    # En PostgreSQL el enum es un tipo propio que drop_table no borra.
    _estado_organizador.drop(op.get_bind(), checkfirst=True)
