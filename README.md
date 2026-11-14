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

## Levantar la app con Docker

Con [Docker](https://docs.docker.com/get-docker/) instalado, el frontend, la API y su base de datos
PostgreSQL se levantan con un solo comando desde la raíz del repositorio, sin instalar Node, Python
ni PostgreSQL:

```bash
docker compose up -d --build                        # construye la imagen y levanta API + base
docker compose exec api python -m scripts.seed      # (opcional) cargar eventos de ejemplo
docker compose logs -f api                          # ver los logs de la API
docker compose down                                 # detener todo (los datos se conservan)
```

La app queda en `http://localhost:8080`. La API también se expone directo en `http://localhost:8000`,
con su documentación interactiva en `http://localhost:8000/docs`. Las migraciones se aplican solas
cada vez que arranca el contenedor de la API.

- `backend/Dockerfile` define la imagen de la API.
- `frontend/Dockerfile` construye el frontend y lo sirve con nginx (`frontend/nginx/default.conf.template`),
  que además reenvía `/api/*` a la API sacándole el prefijo y reescribe el path de la cookie del
  refresh token (`/auth` → `/api/auth`), igual que el proxy de Vite en desarrollo.
- `compose.yaml` define los tres servicios (`web`, `api` y `db`) y el volumen `pgdata` donde persisten
  los datos. Para borrar también los datos: `docker compose down -v`.

Para desarrollar con recarga automática se puede levantar solo la base (`docker compose up -d db`) y
correr la API con Poetry como se explica en la sección Backend.

## Deploy en un PaaS (Render, Railway, Fly)

Se despliegan dos servicios Docker desde este repositorio, más una base PostgreSQL administrada del
proveedor:

| Servicio | Carpeta (Dockerfile) | Variables de entorno |
|---|---|---|
| `api` | `backend/` | `DATABASE_URL`, `JWT_SECRET_KEY`, `COOKIE_SECURE=true`, `COOKIE_DOMAIN` vacío, `NOMINATIM_USER_AGENT` (con un contacto real). Ver `backend/.env.example` |
| `web` | `frontend/` | `API_UPSTREAM`: URL de la API **sin barra final**. Puede ser la interna del proveedor (por ejemplo `http://api.railway.internal:8000` o `http://<app>.internal:8000` en Fly) o la pública (`https://...`) |

- **El dominio que usa la gente es el de `web`.** El navegador le habla solo a nginx, que reenvía
  `/api` a la API. Front y API quedan en el mismo origen, que es lo que necesita la cookie del
  refresh token (`httponly`, `SameSite=lax`, sin dominio). No hace falta configurar CORS.
- `DATABASE_URL` tiene que usar el esquema `postgresql+asyncpg://`. Los proveedores suelen dar
  `postgres://...` o `postgresql://...`, y hay que cambiarle el prefijo.
- Las dos imágenes escuchan en el puerto de la variable `PORT` si el proveedor la inyecta
  (8080 para `web` y 8000 para `api` si no).

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
