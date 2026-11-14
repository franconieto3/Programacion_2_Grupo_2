# Programacion_2_Grupo_2

## Backend

El backend (FastAPI) se gestiona con [Poetry](https://python-poetry.org/) (>= 2.0).

```bash
cd backend
poetry install                               # crea backend/.venv e instala dependencias + grupo dev
cp .env.example .env                         # completar variables de entorno (JWT_SECRET_KEY es obligatoria)
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
correr la API con Poetry como se explica en la sección Backend. La base se publica solo en
`127.0.0.1:5432`. Si ese puerto ya está ocupado (por ejemplo, por un PostgreSQL instalado), se
elige otro con `DB_PUERTO_HOST=5433 docker compose up -d`, y en el `.env` hay que usar ese puerto
en `DATABASE_URL`.

La imagen de la API instala exactamente las versiones de `backend/poetry.lock`: el `Dockerfile` las
exporta con Poetry a un `requirements.txt` con hashes. Si se cambian dependencias en
`pyproject.toml` sin actualizar el lock (`poetry lock`), el build falla.

El `compose.yaml` es solo para desarrollo y demos: tiene contraseñas y un `JWT_SECRET_KEY` de
desarrollo escritos en el archivo. En producción la configuración se carga en el proveedor (ver
abajo).

## Deploy en un PaaS (Render, Railway, Fly)

Se despliegan dos servicios Docker desde este repositorio, más una base PostgreSQL administrada del
proveedor:

| Servicio | Carpeta (Dockerfile) | Variables de entorno |
|---|---|---|
| `api` | `backend/` | `DATABASE_URL`, `JWT_SECRET_KEY` (propia de producción, distinta de la de desarrollo; la API no arranca sin ella), `COOKIE_SECURE=true`, `COOKIE_DOMAIN` vacío, `NOMINATIM_USER_AGENT` (con un contacto real). Ver `backend/.env.example` |
| `web` | `frontend/` | `API_UPSTREAM`: URL de la API **sin barra final**. Puede ser la interna del proveedor (por ejemplo `http://api.railway.internal:8000` o `http://<app>.internal:8000` en Fly) o la pública (`https://...`) |

- **El dominio que usa la gente es el de `web`.** El navegador le habla solo a nginx, que reenvía
  `/api` a la API. Front y API quedan en el mismo origen, que es lo que necesita la cookie del
  refresh token (`httponly`, `SameSite=lax`, sin dominio). No hace falta configurar CORS.
- `DATABASE_URL` tiene que usar el esquema `postgresql+asyncpg://`. Los proveedores suelen dar
  `postgres://...` o `postgresql://...`, y hay que cambiarle el prefijo.
- Las dos imágenes escuchan en el puerto de la variable `PORT` si el proveedor la inyecta
  (8080 para `web` y 8000 para `api` si no).

### Alta de administradores

Los administradores se asignan a mano en la base: no hay endpoint ni pantalla para crearlos, a
propósito. Un usuario es administrador si tiene una fila en la tabla `administradores`.

1. La persona se registra desde la app, como cualquier usuario.
2. Desde la consola SQL del proveedor (o con `psql` y la URL de la base), se corre:

   ```sql
   INSERT INTO administradores (id_usuario)
   SELECT id_usuario FROM usuario WHERE email = '<email>'
   ON CONFLICT (id_usuario) DO NOTHING;
   ```

   `id_admin` y `fecha_alta` los completa la base (`gen_random_uuid()` y `now()`; el default de
   `id_admin` lo agrega la migración `0005_administradores_id_default`). Repetir la consulta no
   duplica nada. Si responde `INSERT 0 0` y la persona todavía no era administradora, el email no
   está registrado.
3. La persona recarga la página y le aparece "Administración" en la barra. El permiso se consulta
   en la base en cada request, así que no hace falta reiniciar nada.

Para quitarle el rol: `DELETE FROM administradores WHERE id_usuario = (SELECT id_usuario FROM usuario WHERE email = '<email>');`

Con el `compose.yaml` local, la consola SQL es `docker compose exec db psql -U postgres -d eventos`.

## Integración continua

`.github/workflows/pipeline.yaml` corre en cada push y pull request, con tres jobs en paralelo:

- **Tests del backend:** `poetry run pytest`.
- **Lint y build del frontend:** `npm run lint` y `npm run build`.
- **Imágenes Docker:** construye las dos imágenes con `docker compose up -d --build` y prueba la app
  completa a través de nginx: que la API responda en `/api`, que la SPA devuelva `index.html` en
  una ruta profunda y que el login setee la cookie del refresh token con `Path=/api/auth`. Detecta
  un Dockerfile roto o un `poetry.lock` desactualizado. Las imágenes no se publican.

El resultado se ve en la pestaña *Actions* del repositorio.

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

### Arquitectura del frontend

**Stack:** React 19 + Vite (JavaScript), React Router 7 para las rutas, TanStack Query 5 para los
datos del servidor y Leaflet (react-leaflet) con tiles de OpenStreetMap para los mapas.

```
frontend/src/
├── main.jsx, App.jsx      arranque, QueryClientProvider y definición de las rutas
├── queryClient.js         configuración de la caché de TanStack Query
├── services/              acceso a la API: client.js + un módulo por recurso
├── routes/                PrivateRoute, OrganizadorRoute y AdminRoute (guardas de acceso)
├── pages/                 una página por ruta (Explorar, DetalleEvento, MisEventos, ...)
├── features/              lógica por dominio: componentes y hooks propios
│   ├── auth/              AuthContext (sesión) y formularios de login y registro
│   ├── eventos/           búsqueda, filtros, formulario, tarjetas, permisos
│   ├── organizadores/     solicitud y administración de organizadores
│   └── ubicacion/         ubicación inicial, buscador de lugar y selector de punto
├── components/            piezas reutilizables sin lógica de dominio
│   ├── ui/                Button, Input, FormField, ConfirmDialog, Badge, ...
│   ├── layout/            Layout, BarraNavegacion y MenuCuenta
│   └── mapa/              componente Mapa compartido
└── hooks/                 hooks genéricos (useFormSubmit, useDebounce)
```

**Cómo fluyen los datos:**
- `services/client.js` es el **único módulo que usa `fetch`**. Arma la URL (`VITE_API_URL`, por
  defecto `/api`), agrega el access token, convierte los errores del backend en `ApiError` y, ante
  un `401`, renueva la sesión una vez y reintenta. Cada recurso tiene su módulo en `services/`
  (`eventos.js`, `categorias.js`, `organizadores.js`, ...).
- Las **lecturas** pasan por hooks de TanStack Query de cada dominio (`useBusquedaEventos`,
  `useEvento`, `useMisEventos`, `useOrganizadores`, ...). La caché evita que una respuesta vieja
  pise a una nueva cuando se arrastra el mapa.
- Las **escrituras** (crear, editar, cancelar u ocultar un evento, resolver una solicitud) llaman
  al servicio desde la página o el componente y después invalidan las claves de la caché afectadas
  (por ejemplo, todas las de eventos después de crear uno), así las listas se vuelven a pedir.
- El mapa y la lista de `/explorar` comparten el mismo `useBusquedaEventos`, así nunca muestran
  resultados distintos. El viewport y los filtros quedan en la URL.

**Sesión:**
- El access token vive **solo en memoria** (no en `localStorage`), para que un script inyectado no
  pueda leerlo. Al recargar la página, `AuthContext` lo recupera con la cookie `httpOnly` del
  refresh token (`POST /auth/verify-session`) y pide el usuario con sus roles (`GET /auth/me`).
- `useAuth()` expone el usuario, `login`, `logout` y `refrescarUsuario`. Las guardas de `routes/`
  usan esos roles: `PrivateRoute` exige sesión, `OrganizadorRoute` un perfil de organizador
  `APROBADO` y `AdminRoute` ser administrador. El backend valida igual cada request.
- La cookie del refresh token tiene path `/auth` en el backend. Como el navegador ve esas rutas como
  `/api/auth`, el proxy reescribe el path: Vite en desarrollo y nginx en producción. Por eso front y
  API tienen que estar bajo el mismo origen.

El detalle de cada pantalla y de las decisiones tomadas está en
[`docs/08-hoja-de-ruta-frontend.md`](docs/08-hoja-de-ruta-frontend.md).
