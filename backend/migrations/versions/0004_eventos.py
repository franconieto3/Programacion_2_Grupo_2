"""tablas de eventos: categoria_evento (con el catalogo cargado), lugar,
eventos y evento_categoria

Revision ID: 0004_eventos
Revises: 0003_administradores
Create Date: 2026-10-20

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004_eventos"
down_revision: Union[str, None] = "0003_administradores"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_estado_evento = sa.Enum(
    "BORRADOR", "PUBLICADO", "CANCELADO", "OCULTO", name="estado_evento"
)
_origen_evento = sa.Enum(
    "CARGA_ORGANIZADOR", "SEED_EQUIPO", name="origen_evento"
)

# Catalogo cerrado de RF-04.1. Se carga aca y no en un script de seed porque
# forma parte del esquema: cualquier base migrada tiene que tenerlo.
_CATEGORIAS = [
    ("bar", "Bar", "Bares, pubs y cervecerias."),
    ("recital", "Recital", "Musica en vivo y conciertos."),
    ("teatro", "Teatro", "Obras de teatro, stand-up y espectaculos escenicos."),
    ("cine", "Cine", "Proyecciones, ciclos y festivales de cine."),
    ("deportivo", "Deportivo", "Partidos, carreras y actividades deportivas."),
    ("museo", "Museo", "Museos, muestras y exposiciones."),
    ("gastronomia", "Gastronomia", "Ferias de comida, degustaciones y restaurantes."),
    ("feria", "Feria", "Ferias de diseno, artesanias y mercados."),
    ("taller", "Taller", "Talleres, cursos y clases abiertas."),
    ("aire-libre", "Aire libre", "Actividades en parques, plazas y espacios abiertos."),
    ("otro", "Otro", "Eventos que no encajan en las demas categorias."),
]


def _uuid_type():
    return sa.String(36).with_variant(postgresql.UUID(as_uuid=True), "postgresql")


def upgrade() -> None:
    categoria_evento = op.create_table(
        "categoria_evento",
        sa.Column("id_categoria", sa.Integer, primary_key=True),
        sa.Column("slug", sa.String(50), nullable=False, unique=True),
        sa.Column("nombre", sa.String(100), nullable=False),
        sa.Column("descripcion", sa.Text, nullable=True),
        sa.Column("activa", sa.Boolean, nullable=False, server_default=sa.true()),
    )
    op.bulk_insert(
        categoria_evento,
        [
            {"slug": slug, "nombre": nombre, "descripcion": descripcion, "activa": True}
            for slug, nombre, descripcion in _CATEGORIAS
        ],
    )

    op.create_table(
        "lugar",
        sa.Column("id_lugar", _uuid_type(), primary_key=True),
        sa.Column("nombre", sa.String(255), nullable=True),
        sa.Column("direccion", sa.String(255), nullable=True),
        sa.Column("latitud", sa.Float, nullable=False),
        sa.Column("longitud", sa.Float, nullable=False),
    )
    # Filtro por viewport (RF-03.3).
    op.create_index("ix_lugar_latitud_longitud", "lugar", ["latitud", "longitud"])

    op.create_table(
        "eventos",
        sa.Column("id_evento", _uuid_type(), primary_key=True),
        # NULL en los eventos de seed (RF-05.2), que no tienen organizador.
        sa.Column(
            "id_organizador",
            _uuid_type(),
            sa.ForeignKey("organizadores.id_organizador"),
            nullable=True,
        ),
        sa.Column(
            "id_lugar",
            _uuid_type(),
            sa.ForeignKey("lugar.id_lugar"),
            nullable=False,
        ),
        sa.Column("titulo", sa.String(255), nullable=False),
        sa.Column("descripcion", sa.Text, nullable=False),
        sa.Column("fecha_inicio", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fecha_fin", sa.DateTime(timezone=True), nullable=True),
        sa.Column("hora_inicio_local", sa.Time, nullable=False),
        sa.Column("precio", sa.Numeric(10, 2), nullable=True),
        sa.Column("estado", _estado_evento, nullable=False),
        sa.Column("origen", _origen_evento, nullable=False),
        sa.Column("fecha_publicacion", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "fecha_actualizacion",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_eventos_id_organizador", "eventos", ["id_organizador"])
    op.create_index("ix_eventos_id_lugar", "eventos", ["id_lugar"])
    # Regla de visibilidad de la busqueda (estado + fecha).
    op.create_index(
        "ix_eventos_estado_fecha_inicio", "eventos", ["estado", "fecha_inicio"]
    )

    op.create_table(
        "evento_categoria",
        sa.Column(
            "id_evento",
            _uuid_type(),
            sa.ForeignKey("eventos.id_evento", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "id_categoria",
            sa.Integer,
            sa.ForeignKey("categoria_evento.id_categoria"),
            primary_key=True,
        ),
    )


def downgrade() -> None:
    op.drop_table("evento_categoria")
    op.drop_table("eventos")
    op.drop_table("lugar")
    op.drop_table("categoria_evento")
    # En PostgreSQL los enums son tipos propios que drop_table no borra.
    _estado_evento.drop(op.get_bind(), checkfirst=True)
    _origen_evento.drop(op.get_bind(), checkfirst=True)
