"""tablas del modulo de autenticacion (usuario, refresh_token,
password_reset_token, audit_log)

Revision ID: 0001_auth_tables
Revises:
Create Date: 2026-09-20

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_auth_tables"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _uuid_type():
    return sa.String(36).with_variant(postgresql.UUID(as_uuid=True), "postgresql")


def upgrade() -> None:
    op.create_table(
        "usuario",
        sa.Column("id_usuario", _uuid_type(), primary_key=True),
        sa.Column("nombre", sa.String(255), nullable=False),
        sa.Column("apellido", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=True),
        sa.Column(
            "fecha_creacion",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("activo", sa.Boolean, nullable=False, server_default=sa.true()),
    )
    op.create_index("ix_usuario_email", "usuario", ["email"])

    op.create_table(
        "refresh_token",
        sa.Column("id", _uuid_type(), primary_key=True),
        sa.Column("usuario_id", _uuid_type(), sa.ForeignKey("usuario.id_usuario"), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_refresh_token_usuario_id", "refresh_token", ["usuario_id"])
    op.create_index("ix_refresh_token_token_hash", "refresh_token", ["token_hash"])

    op.create_table(
        "password_reset_token",
        sa.Column("id", _uuid_type(), primary_key=True),
        sa.Column("usuario_id", _uuid_type(), sa.ForeignKey("usuario.id_usuario"), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_password_reset_token_usuario_id", "password_reset_token", ["usuario_id"]
    )
    op.create_index(
        "ix_password_reset_token_token_hash", "password_reset_token", ["token_hash"]
    )

    op.create_table(
        "audit_log",
        sa.Column("id", _uuid_type(), primary_key=True),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("detalle", sa.String(500), nullable=False, server_default=""),
        sa.Column("ocurrido_en", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_audit_log_event_type", "audit_log", ["event_type"])
    op.create_index("ix_audit_log_email", "audit_log", ["email"])


def downgrade() -> None:
    op.drop_table("audit_log")
    op.drop_table("password_reset_token")
    op.drop_table("refresh_token")
    op.drop_table("usuario")
