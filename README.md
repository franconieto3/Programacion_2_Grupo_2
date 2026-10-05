# Programacion_2_Grupo_2

## Backend

El backend (FastAPI) se gestiona con [Poetry](https://python-poetry.org/) (>= 2.0).

```bash
cd backend
poetry install                               # crea backend/.venv e instala dependencias + grupo dev
cp .env.example .env                         # completar variables de entorno
poetry run alembic upgrade head              # aplicar migraciones
poetry run uvicorn app.main:app --reload     # levantar la API
poetry run pytest                            # correr los tests
```

Para agregar dependencias: `poetry add <paquete>` (o `poetry add --group dev <paquete>` para desarrollo).
