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

## Levantar la API con Docker

Con [Docker](https://docs.docker.com/get-docker/) instalado, la API y su base de datos PostgreSQL
se levantan con un solo comando desde la raíz del repositorio, sin instalar Python ni PostgreSQL:

```bash
docker compose up -d --build                        # construye la imagen y levanta API + base
docker compose exec api python -m scripts.seed      # (opcional) cargar eventos de ejemplo
docker compose logs -f api                          # ver los logs de la API
docker compose down                                 # detener todo (los datos se conservan)
```

La API queda en `http://localhost:8000` y su documentación interactiva en `http://localhost:8000/docs`.
Las migraciones se aplican solas cada vez que arranca el contenedor de la API.

- `backend/Dockerfile` define la imagen de la API.
- `compose.yaml` define los dos servicios (`api` y `db`) y el volumen `pgdata` donde persisten los datos.
  Para borrar también los datos: `docker compose down -v`.

Para desarrollar con recarga automática se puede levantar solo la base (`docker compose up -d db`) y
correr la API con Poetry como se explica en la sección Backend.

## Integración continua

`.github/workflows/pipeline.yaml` corre en cada push y pull request: ejecuta los tests del backend
(`poetry run pytest`) y el linter y el build del frontend. El resultado se ve en la pestaña *Actions*
del repositorio.

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
