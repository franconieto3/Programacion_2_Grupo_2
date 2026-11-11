# Programacion_2_Grupo_2

## Backend

El backend (FastAPI) se gestiona con [Poetry](https://python-poetry.org/) (>= 2.0).

```bash
cd backend
poetry install                               # crea backend/.venv e instala dependencias + grupo dev
cp .env.example .env                         # completar variables de entorno
poetry run alembic upgrade head              # aplicar migraciones
poetry run python -m scripts.seed            # cargar eventos de ejemplo (--reset para recargarlos)
poetry run uvicorn app.main:app --reload     # levantar la API
poetry run pytest                            # correr los tests
```

Para agregar dependencias: `poetry add <paquete>` (o `poetry add --group dev <paquete>` para desarrollo).

## Frontend

El frontend es una app React + Vite (JavaScript) gestionada con npm.

```bash
cd frontend
npm install        # instalar dependencias
npm run dev        # levantar el servidor de desarrollo (http://localhost:5173)
npm run build      # build de producción en frontend/dist
npm run lint       # linter
```

En desarrollo, Vite reenvía todo lo que empiece con `/api` al backend sacándole el prefijo
(`fetch('/api/eventos')` → `http://localhost:8000/eventos`), así que hay que levantar el backend también.
Si el backend corre en otro puerto, crear `frontend/.env.local` con `API_PROXY_TARGET=http://localhost:<puerto>`.
