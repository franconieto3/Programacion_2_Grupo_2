from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Categoria(Base):
    """Catalogo cerrado de categorias de eventos (RF-04.1). Lo carga la
    migracion 0004; la API no permite crear categorias.

    PK entera y no UUID: es un catalogo chico y fijo, no un recurso cuyo
    volumen haya que ocultar (RNF-04.3). Hacia afuera se identifica por
    `slug`, que es estable y legible en una URL (?categorias=aire-libre).

    `activa` permite retirar una categoria sin borrarla (RF-04.3): las
    inactivas no se listan ni se pueden asignar a un evento nuevo, pero los
    eventos que ya la tenian la conservan."""

    __tablename__ = 'categoria_evento'

    id_categoria: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    activa: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
