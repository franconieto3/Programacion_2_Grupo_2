from pydantic import BaseModel, ConfigDict


class CategoriaPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    slug: str
    nombre: str
    descripcion: str | None
