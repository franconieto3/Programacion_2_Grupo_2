"""tabla administradores (perfil de administrador)

Revision ID: 0003_administradores
Revises: 0002_organizadores
Create Date: 2026-10-20

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003_administradores"
down_revision: Union[str, None] = "0002_organizadores"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _uuid_type():
    return sa.String(36).with_variant(postgresql.UUID(as_uuid=True), "postgresql")


def upgrade() -> None:
    op.create_table(
        "administradores",
        sa.Column("id_admin", _uuid_type(), primary_key=True),
        # UNIQUE: un usuario es administrador o no lo es (multiplicidad 0..1).
        sa.Column(
            "id_usuario",
            _uuid_type(),
            sa.ForeignKey("usuario.id_usuario", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "fecha_alta",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    op.drop_table("administradores")
