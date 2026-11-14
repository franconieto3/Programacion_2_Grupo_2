"""administradores.id_admin con default gen_random_uuid() en la base

Hasta ahora el id lo generaba solo la app (default de Python en el modelo),
asi que un INSERT hecho a mano desde la consola SQL (el alta manual de
administradores, ver README) tenia que pasar id_admin explicito. Con este
default alcanza con `INSERT INTO administradores (id_usuario) ...`.

Revision ID: 0005_administradores_id_default
Revises: 0004_eventos
Create Date: 2026-11-14

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005_administradores_id_default"
down_revision: Union[str, None] = "0004_eventos"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _es_postgresql() -> bool:
    # gen_random_uuid() es nativa de PostgreSQL desde la version 13. En
    # SQLite (pruebas manuales) id_admin es String(36), la funcion no existe
    # y el id lo sigue generando la app: no hay nada que cambiar.
    return op.get_bind().dialect.name == "postgresql"


def upgrade() -> None:
    if not _es_postgresql():
        return
    op.alter_column(
        "administradores",
        "id_admin",
        server_default=sa.text("gen_random_uuid()"),
    )


def downgrade() -> None:
    if not _es_postgresql():
        return
    op.alter_column("administradores", "id_admin", server_default=None)
