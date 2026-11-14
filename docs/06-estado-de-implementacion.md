# Estado de implementación

## Plataforma de descubrimiento de eventos por geolocalización

**Fecha de relevamiento:** 14/11/2026 · **Rama:** `franco/deploy-frontend` (deploy del frontend, sobre `9ccb8da`, merge del PR #17)

---

## Resumen

Están implementados el **backend** (FastAPI + SQLAlchemy + PostgreSQL) y el **frontend** (React 19 +
Vite, React Router 7, TanStack Query 5, Leaflet), más la infraestructura para levantarlos con Docker
y desplegarlos en un PaaS.

- **Backend:** módulos de autenticación (`auth`), organizadores y administradores (solicitud,
  aprobación, rechazo y suspensión de organizadores), categorías, eventos (búsqueda por viewport,
  ficha de detalle, mis eventos, alta, edición, cancelación y ocultamiento por un administrador),
  geocodificación (búsqueda de lugares en Nominatim) y configuración (ubicación por defecto), más un
  script de seed de eventos. Hay 5 migraciones (`0001_auth_tables` a `0005_administradores_id_default`).
- **Frontend:** registro y login, exploración con mapa y lista sincronizados, filtros, buscador de
  lugar, ficha de detalle, solicitud de organizador, alta/edición/cancelación de eventos, mis
  eventos y administración (ocultar eventos y gestionar organizadores). El detalle de cada pantalla
  está en `08-hoja-de-ruta-frontend.md`.
- **Infraestructura:** imágenes Docker de la API y del frontend (nginx como proxy de `/api`),
  `compose.yaml` para desarrollo y pipeline de CI con tres jobs (ver [Infraestructura, CI y
  deploy](#infraestructura-ci-y-deploy)).

| Ítem | Estado |
|---|---|
| Requisitos funcionales **Must** implementados | **23 de 23** (ver `02-requisitos-funcionales.md`), en backend y frontend |
| Requisitos **Should** implementados | RF-05.5 (administración de organizadores) |
| Requisitos funcionales con avance parcial | RF-01.5 (solo preparación del diseño) |
| Casos de uso documentados (CU-01 a CU-04) implementados | **4 de 4** |
| Tests automatizados del backend | 259 funciones de test (347 casos con los parametrizados) en `backend/tests`, 95% de cobertura |
| Tests automatizados del frontend | No hay: quedaron fuera de alcance por decisión del equipo. La CI corre el linter y el build |

---

## Requisitos funcionales

### Implementados

| # | Requisito | Prioridad | Backend | Frontend |
|---|---|---|---|---|
| RF-01.1 | Registrar un usuario con nombre, apellido, email y contraseña | **M** | `POST /auth/register` → `EmailRegister`. Valida email, contraseña de 8 a 128 caracteres y nombre/apellido obligatorios. Rechaza emails duplicados (409). No inicia sesión automáticamente. | `/registro`. Después del alta inicia sesión con los mismos datos. |
| RF-01.2 | Todo usuario registrado puede descubrir eventos | **M** | `GET /eventos` y `GET /eventos/{id_evento}` piden login (`get_usuario_actual`) pero ningún rol: cualquier usuario registrado puede buscar eventos y ver su ficha, sea organizador o no. Sin sesión → `401`. | `/explorar` y `/eventos/:id` dentro de `PrivateRoute`, sin exigir rol. |
| RF-01.3 | Iniciar y cerrar sesión mediante email y contraseña | **M** | `POST /auth/login` → `EmailSignIn` (envuelto en `RateLimitedSignIn`). Devuelve un access token JWT y deja un refresh token en una cookie `httpOnly`. `POST /auth/logout` revoca el refresh token y borra la cookie. `POST /auth/verify-session` permite mantener la sesión (silent refresh). | `/ingresar`. La sesión se restaura al recargar con la cookie (`AuthContext`). "Cerrar sesión" en el menú de la cuenta y en `/perfil`. |
| RF-01.6 | Solicitar convertirse en organizador (nombre público y descripción), queda `PENDIENTE` | **M** | `POST /organizadores/solicitud` → `SolicitarOrganizador` (requiere login). Crea el perfil en `PENDIENTE`. Un usuario tiene como mucho un perfil (`id_usuario` UNIQUE): con una solicitud pendiente o aprobada responde `409`, y si está suspendido, `403`. Un rechazado puede volver a solicitar y se reutiliza la misma fila (flujo 5a de CU-04). | `/organizador/solicitud`: formulario o el estado de la solicitud (en revisión, rechazada, suspendida, aprobada). |
| RF-01.7 | Crear y editar eventos solo con perfil de organizador `APROBADO` | **M** | La dependencia `require_organizador_aprobado` responde `403` si el usuario no tiene perfil de organizador o si su perfil no está `APROBADO` (pendiente, rechazado o suspendido). Protege `POST /eventos`, `GET /eventos/mios`, `PATCH /eventos/{id_evento}` y `POST /eventos/{id_evento}/cancelar`. El estado se consulta en la base en cada request, así que una suspensión corta el acceso de inmediato. | `OrganizadorRoute` protege las rutas de organizador y manda al resto a `/organizador/solicitud`. La barra muestra las acciones solo a organizadores aprobados. |
| RF-02.1 | Alta de un evento con título, descripción, inicio, fin (opcional) y precio (opcional) | **M** | `POST /eventos` → `CrearEvento` (CU-03). El evento queda `PUBLICADO`, con `origen = CARGA_ORGANIZADOR`, asociado al organizador y con `fecha_publicacion`; responde `201` y aparece en "mis eventos". Las fechas deben tener zona horaria; `fecha_fin` tiene que ser posterior al inicio y el inicio tiene que ser futuro; el precio no puede ser negativo. Cualquier dato inválido responde `422`. | `/eventos/nuevo` con `FormularioEvento`. Las fechas se escriben en la zona horaria de la plataforma. |
| RF-02.2 | Ubicar el evento marcando un punto en el mapa (coordenadas como dato autoritativo) | **M** | `lugar` es obligatorio en el alta, con `latitud` (-90 a 90) y `longitud` (-180 a 180); `nombre` y `direccion` son opcionales y descriptivos. Cada alta crea su propio `Lugar`. | `SelectorUbicacion`: pin con clic, arrastre, buscador de lugar o teclado. |
| RF-02.3 | Asociar el evento a una o varias categorías del catálogo | **M** | `categorias` recibe al menos un slug. Se validan contra el catálogo activo con la misma regla que la edición: un slug inexistente o inactivo responde `422`, y los repetidos se ignoran. | `SelectorCategorias` (el mismo de los filtros). |
| RF-02.4 | Editar y dar de baja (cancelar) un evento propio | **M** | `PATCH /eventos/{id_evento}` → `EditarEvento`: edición parcial (solo los campos enviados), `lugar` y `categorias` reemplazan la lista completa, las categorías se validan contra el catálogo activo y `fecha_fin` debe ser posterior al inicio (si no, `422`). Solo se editan eventos `BORRADOR` o `PUBLICADO` (si no, `409`). `POST /eventos/{id_evento}/cancelar` → `CancelarEvento`, válido desde `BORRADOR` o `PUBLICADO`. Ambos exigen ser el organizador dueño (si no, `403`). | `/eventos/:id/editar` manda solo lo que cambió. "Cancelar evento" con confirmación, en la ficha y en mis eventos. |
| RF-02.5 | Listado de "mis eventos" con su estado actual | **M** | `GET /eventos/mios` → `ListarMisEventos`: todos los eventos del organizador, en cualquier estado (incluidos los cancelados y ocultos). | `/mis-eventos`, separado en próximos y finalizados, con el estado de cada evento. |
| RF-03.1 | Vista de mapa centrada en la ubicación del usuario | **M** | Viewport en `GET /eventos` y ubicación por defecto en `GET /config/ubicacion-default` (ver RF-03.3 y RF-03.8). | `/explorar` con Leaflet y tiles de OpenStreetMap. `useUbicacionInicial` pide la geolocalización y, si falla, usa la ubicación por defecto. La posición queda en la URL. |
| RF-03.2 | Vista de lista con los mismos resultados que la vista mapa | **M** | Mapa y lista consumen el mismo `GET /eventos`, que devuelve una página (`items`, `total`, `limit`, `offset`; 20 por defecto, máximo 100) con orden estable por inicio e id. Hay tests de que los mismos parámetros dan siempre el mismo orden y de que recorrer las páginas no repite ni pierde eventos. | Mapa y lista alimentados por el mismo hook (`useBusquedaEventos`), con "Cargar más". |
| RF-03.3 | Desplazar y hacer zoom sobre el mapa, re-ejecutando la búsqueda según el viewport | **M** | `GET /eventos` acepta `lat_min`, `lat_max`, `lng_min` y `lng_max` (filtro `filtrar_por_viewport`, bordes inclusivos). Vienen los cuatro o ninguno y el mínimo no puede superar al máximo, así que no se admiten viewports que crucen el antimeridiano; si no, `422`. Sin viewport no filtra. | Al mover o hacer zoom se vuelve a buscar con debounce. `normalizarViewport()` deja las longitudes en -180..180. |
| RF-03.4 | Filtrar por rango de fechas | **M** | `GET /eventos?desde=&hasta=` (fechas locales, extremos inclusivos, se filtra por el inicio del evento). Cada límite se convierte a UTC con `Settings.zona_horaria`. `desde` posterior a `hasta` → `422`. | `PanelFiltros`. Los filtros quedan en la URL. |
| RF-03.5 | Filtrar por rango horario | **M** | `GET /eventos?hora_desde=&hora_hasta=` (HH:MM, extremos inclusivos) contra `hora_inicio_local`. Si `hora_desde` es posterior a `hora_hasta`, el rango cruza la medianoche (22:00 a 02:00). | `PanelFiltros`. |
| RF-03.6 | Filtrar por una o varias categorías | **M** | `GET /eventos?categorias=bar&categorias=teatro`: coincide un evento con al menos una de las categorías pedidas. Se resuelve con una subconsulta para no duplicar eventos con varias categorías ni romper la paginación. | `SelectorCategorias` en modo filtro. |
| RF-03.7 | Buscar y establecer una ubicación de referencia distinta a la actual | **M** | `GET /geocodificacion/buscar?q=` (requiere login) consulta Nominatim y devuelve sugerencias con su bounding box (`lat_min`/`lat_max`/`lng_min`/`lng_max`, los mismos nombres que el viewport de `GET /eventos`). Sin coincidencias → `[]`; Nominatim caído → `503`. | `BuscadorLugar`: busca desde 3 caracteres y centra el mapa en la sugerencia elegida. |
| RF-03.8 | Uso pleno sin permiso de geolocalización (ubicación por defecto + buscador de lugar) | **M** | `GET /config/ubicacion-default` (público) devuelve `nombre`, `lat`, `lng` y `zoom`, configurables con `UBICACION_DEFAULT_*` y validados al arrancar. El buscador de lugar es `GET /geocodificacion/buscar`. | Sin permiso, el mapa abre en la ubicación por defecto con un aviso que no bloquea y el buscador destacado. |
| RF-03.10 | Ficha de detalle del evento con los datos del organizador | **M** | `GET /eventos/{id_evento}` (requiere login) devuelve el evento y un bloque `organizador` con `id_organizador`, `nombre_publico` y `descripcion` (sin `id_usuario` ni estado del perfil). Un evento de seed trae `{"id_organizador": null, "nombre_publico": "Equipo de la plataforma", ...}`. Visibilidad: PUBLICADO y CANCELADO los ve cualquiera, aunque ya hayan terminado (responde la pregunta abierta #4 de `planning.md`: la búsqueda los oculta, la URL directa no); BORRADOR solo su organizador; OCULTO nadie. Si no se puede ver, 404. | `/eventos/:id`: datos, categorías, mapa chico y "Publicado por". Un 404 muestra "Evento no encontrado". |
| RF-04.1 | Catálogo cerrado de categorías | **M** | La migración `0004_eventos` carga las 11 categorías en `categoria_evento`. `GET /categorias` (público) lista las activas. La API no permite crear categorías. | Se cachea con TanStack Query y lo usan los filtros, el formulario y las tarjetas. |
| RF-04.2 | Asociar múltiples categorías a un evento | **M** | Asociación N:M mediante la tabla `evento_categoria`. Al crear y al editar, `categorias` recibe una lista de slugs (al menos uno). | Las tarjetas y la ficha muestran todas las categorías como chips. |
| RF-05.1 | Un administrador oculta cualquier evento publicado | **M** | `POST /admin/eventos/{id_evento}/ocultar` → `OcultarEvento` (requiere administrador). Válido desde `PUBLICADO` o `CANCELADO` (si no, `409`). Un evento `OCULTO` desaparece de la búsqueda y de la ficha de detalle; su dueño lo sigue viendo en "mis eventos". | "Ocultar evento" en la ficha, solo para administradores, con confirmación. |
| RF-05.2 | Eventos de origen propio (seed) diferenciados | **M** | `Evento.origen` distingue `SEED_EQUIPO` de `CARGA_ORGANIZADOR`. `scripts/seed.py` carga eventos de ejemplo sin organizador mediante `EventoFactory.crear_seed`, repartidos en distintas zonas, fechas, horarios y categorías (`--reset` borra el seed y lo recarga). | `BadgeEquipo` ("Equipo de la plataforma") en las tarjetas y en la ficha. |
| RF-05.5 | Un administrador aprueba, rechaza y suspende perfiles de organizador | **S** | `GET /admin/organizadores?estado=` lista los perfiles en un estado. `POST /admin/organizadores/{id}/aprobar` y `/rechazar` son válidos desde `PENDIENTE`; `/suspender`, desde `APROBADO`. Una transición inválida responde `409`. | `/admin/organizadores` con una pestaña por estado, protegida por `AdminRoute`. |

### Parcialmente preparados

| # | Requisito | Prioridad | Estado |
|---|---|---|---|
| RF-01.5 | Autenticación mediante proveedores externos (login social) | **C** | **No implementado**, aunque el diseño lo contempla: `password_hash` es nullable, `Auth` se arma con estrategias intercambiables (Strategy) y existe `UnsupportedRecovery` (Null Object) para proveedores sin contraseña local. No hay endpoints ni integración con Google/Facebook. |

### Pendientes

| Grupo | Requisitos |
|---|---|
| RF-01 · Cuentas | RF-01.4 (editar perfil), RF-01.8 |
| RF-02 · Gestión de eventos | RF-02.6 a RF-02.10 |
| RF-03 · Descubrimiento y búsqueda | RF-03.9, RF-03.11 a RF-03.14 |
| RF-04 · Categorías | RF-04.3 (el modelo ya tiene `activa` para retirar una categoría sin borrarla, pero no hay endpoints de administración) |
| RF-05 · Moderación | RF-05.3, RF-05.4 |
| RF-06 · Ingesta externa | RF-06.1 |
| RF-07 · Monetización | RF-07.1, RF-07.2 |

### Funcionalidad implementada que no figura como RF

| Funcionalidad | Detalle |
|---|---|
| Solicitud de recuperación de contraseña | `POST /auth/recover-password` → `EmailRecovery`. Genera un token de un solo uso (60 min), guarda su hash en `password_reset_token` y envía el link por email. **Quedó a medias y fuera de alcance por decisión del equipo:** no hay un endpoint que consuma el token y cambie la contraseña (`used_at` nunca se escribe), y el frontend no ofrece la opción. |
| Registro de auditoría | `AuditLogObserver` escribe en `audit_log` los 5 eventos de auth: `user_registered`, `login_succeeded`, `login_failed`, `password_recovery_requested` y `session_verified`. |
| Emails transaccionales | `EmailNotificationObserver` envía un email de bienvenida al registrarse y el link de recuperación. Hoy usa `ConsoleEmailSender`, que solo los escribe en el log. |
| Usuario actual con sus roles | `GET /auth/me` (`app/perfil/router.py`): datos del usuario autenticado, su perfil de organizador (`id_organizador`, `nombre_publico`, `estado`) o `null`, y `es_admin`. Lo usa el frontend después del login y al restaurar la sesión para mostrar u ocultar las acciones de organizador y de administrador. Sin token `401`, cuenta inactiva `403`. En el frontend, `/perfil` muestra los datos de la cuenta y los roles. |
| Errores de validación en español | `app/core/validation_errors.py`: handler de `RequestValidationError` que traduce el `msg` de cada error según su `type` de Pydantic y mantiene el formato `{"detail": [{loc, msg, type}]}`. Los validadores propios conservan su texto y un tipo sin traducción conserva el mensaje original. No devuelve `input` ni `ctx`. El frontend los muestra en cada campo (`useFormSubmit`). |
| Alta de administradores | Por decisión del equipo, se asignan a mano en la base (fila en `administradores`); no hay endpoint ni pantalla. El procedimiento está en el README ("Alta de administradores"). |

---

## Requisitos no funcionales cubiertos

| # | Requisito | Cómo se cubre |
|---|---|---|
| RNF-04.1 | Contraseñas con hashing seguro | `Argon2PasswordHasher` (argon2) |
| RNF-04.2 | Autenticación por JWT, access token en memoria del cliente | El access token viaja en el cuerpo de la respuesta y el frontend lo guarda solo en memoria (`src/services/client.js`, nunca en `localStorage`). El refresh token va en una cookie `httpOnly` con path `/auth`, que el proxy (Vite en desarrollo, nginx en producción) reescribe a `/api/auth`. |
| RNF-04.3 | Identificadores no secuenciales (UUID) | PK UUID en todas las entidades (usuarios, perfiles, eventos, lugares, tokens, auditoría). La excepción es `categoria_evento`, con una PK entera interna: la API identifica las categorías por `slug`. |
| RNF-04 (general) | Mitigación de fuerza bruta y enumeración | Bloqueo tras 5 intentos fallidos en 15 min (`RateLimitedSignIn`, devuelve 423). Respuestas idénticas en la recuperación de contraseña, exista o no el email. |
| RNF-04 (general) | Secreto de firma de los tokens | La API no arranca si `JWT_SECRET_KEY` falta, tiene menos de 32 caracteres o es un valor de ejemplo del repo (`field_validator` en `app/core/config.py`). Los errores de configuración no imprimen el valor rechazado (`hide_input_in_errors`). |
| RNF-01.4 | Caché local de las búsquedas de lugares | `CachedGeocodificador` (Decorator, `app/geocodificacion/decorators/cached.py`): caché en memoria por proceso, con TTL y tope de entradas configurables (`GEOCODIFICACION_CACHE_TTL_SEGUNDOS`, `GEOCODIFICACION_CACHE_MAX_ENTRADAS`). No cachea errores. |
| RNF-05.1 | Política de uso de Nominatim | `RateLimitedGeocodificador` (Decorator) espacia las requests salientes a ≥1 s (las que llegan antes esperan, no se rechazan); `User-Agent` configurable en `Settings.nominatim_user_agent`. `GET /geocodificacion/buscar` requiere login, así la API no queda como proxy anónimo. Límite conocido: el estado es por proceso (un único worker). |
| RNF-05.2 | PostgreSQL en dev/prod, SQLite solo en tests | `database_url` por defecto en PostgreSQL; el `compose.yaml` levanta PostgreSQL 16. Los tests usan `aiosqlite`. |
| RNF-04.4 | Moderación restringida a administradores | Tabla `administradores` (migración `0003_administradores`): un usuario es administrador si tiene una fila ahí, y `Usuario` sigue sin rol. `get_admin_actual` protege todo `/admin/...`: sin sesión `401`, sin perfil de administrador `403`. En el frontend, `AdminRoute`. Los administradores se cargan a mano en la base. |
| RNF-05.3 | FastAPI + OpenAPI + Pydantic | Schemas Pydantic en los `schemas.py` de cada módulo. Documentación interactiva en `/docs`. |

---

## Casos de uso

### Casos de uso documentados (`04-casos-de-uso.md`)

| Caso de uso | Estado | Observación |
|---|---|---|
| CU-01 · Usuario descubre eventos cerca de su ubicación actual | ✅ Implementado | `/explorar`: el mapa se centra en la ubicación del usuario y muestra los eventos del viewport en el mapa y en la lista. Flujo 3a (permiso rechazado): abre en la ubicación por defecto (`GET /config/ubicacion-default`) con el buscador de lugar destacado. |
| CU-02 · Usuario explora eventos en una ubicación distinta | ✅ Implementado | `BuscadorLugar` consulta `GET /geocodificacion/buscar?q=` y centra el mapa en la sugerencia elegida, que dispara la búsqueda por viewport. Sin coincidencias → "sin coincidencias"; Nominatim caído (`503`) → "el buscador no está disponible". |
| CU-03 · Organizador publica un nuevo evento | ✅ Implementado | `/eventos/nuevo`: formulario, pin en el mapa y categorías (pasos 1 a 6). `POST /eventos` valida los datos, guarda el evento `PUBLICADO` y el evento aparece en "mis eventos" (pasos 7 a 9). Flujo 8a: los datos inválidos se marcan en cada campo (`422`). Flujos 9a y 9b: edición y cancelación. |
| CU-04 · Usuario solicita convertirse en organizador | ✅ Implementado | `/organizador/solicitud` crea el perfil en `PENDIENTE` (paso 4). El administrador lo aprueba o rechaza en `/admin/organizadores` (pasos 5 y 6); un rechazado puede volver a solicitar (flujo 5a). El usuario ve el resultado en la app al volver a la página de solicitud o al recargar; no se manda email. |

### Flujos de autenticación implementados

Estos flujos no están documentados como casos de uso formales, pero son los que hoy resuelve el
sistema. Todos los endpoints están bajo el prefijo `/auth`.

#### Registrarse (RF-01.1) · `POST /auth/register`

- **Flujo principal:** el usuario envía nombre, apellido, email y contraseña → el sistema hashea la
  contraseña, crea el usuario, publica `UserRegistered` (email de bienvenida y auditoría) y responde
  `201` con los datos públicos del usuario.
- **Alternativos:** datos inválidos → `422`. Email ya registrado → `409`.

#### Iniciar sesión (RF-01.3) · `POST /auth/login`

- **Flujo principal:** el usuario envía email y contraseña → el sistema valida las credenciales,
  emite un access token (15 min) y un refresh token (14 días, se guarda su hash en `refresh_token`),
  publica `LoginSucceeded` y responde con el access token y los datos del usuario. El refresh
  token queda en una cookie `httpOnly`.
- **Alternativos:** email inexistente o contraseña incorrecta → `401` con un mensaje genérico.
  Cuenta inactiva → `403` (solo se revela después de validar la contraseña). 5 fallos en 15 min →
  `423`. Todos los fallos publican `LoginFailed`.

#### Verificar sesión / silent refresh (RF-01.3) · `POST /auth/verify-session`

- **Flujo principal:** si llega un access token en el header `Authorization`, se valida y se
  devuelven los datos de la sesión. Si no llega, pero sí la cookie de refresh, se valida contra
  `refresh_token` y se emite un **access token nuevo**. En ambos casos se publica `SessionVerified`.
- **Alternativos:** sin tokens → `401`. Token inválido, revocado o vencido, o usuario
  inactivo → `401`.

#### Usuario actual · `GET /auth/me`

- **Flujo principal:** con un access token válido en `Authorization`, responde los datos públicos
  del usuario más `organizador` (`{ id_organizador, nombre_publico, estado }` o `null`) y
  `es_admin`. No acepta la cookie de refresh: si el token venció, el cliente renueva la sesión con
  `verify-session` y reintenta.
- **Alternativos:** sin token o token inválido → `401`. Cuenta inactiva → `403`.

#### Cerrar sesión (RF-01.3) · `POST /auth/logout`

- **Flujo principal:** el sistema marca el refresh token como revocado (`revoked_at`), borra la
  cookie y responde `204`.

#### Solicitar recuperación de contraseña · `POST /auth/recover-password`

- **Flujo principal:** el usuario envía su email → si la cuenta existe, se guarda un token de
  reset (60 min) y se envía el link por email. Se publica `PasswordRecoveryRequested`.
- **Respuesta:** siempre `202` con el mismo mensaje, exista o no la cuenta (evita la enumeración
  de usuarios).
- **Fuera de alcance:** el endpoint para restablecer la contraseña con el token. El frontend no
  ofrece este flujo.

---

## Infraestructura, CI y deploy

| Pieza | Dónde | Qué resuelve |
|---|---|---|
| Imagen de la API | `backend/Dockerfile` | Instala exactamente las versiones de `poetry.lock` (exportadas a un `requirements.txt` con hashes). Al arrancar aplica las migraciones y levanta uvicorn en `${PORT:-8000}`. |
| Imagen del frontend | `frontend/Dockerfile`, `frontend/nginx/default.conf.template` | Build de Vite servido con nginx. nginx reenvía `/api/*` a la API (`API_UPSTREAM`) sacando el prefijo, reescribe el path de la cookie del refresh token a `/api/auth`, devuelve `index.html` en las rutas de la SPA y vuelve a resolver el DNS de la API cada 10 s. Front y API quedan en el mismo origen. |
| Entorno de desarrollo | `compose.yaml` | `web`, `api` y `db` (PostgreSQL 16) con `docker compose up -d --build`; la app queda en `http://localhost:8080`. Solo para desarrollo y demos: tiene secretos de desarrollo escritos en el archivo. |
| Integración continua | `.github/workflows/pipeline.yaml` | Tres jobs en cada push y PR: tests del backend, lint y build del frontend, y construcción de las imágenes con una prueba de punta a punta a través de nginx. |
| Deploy | README, "Deploy en un PaaS" | Dos servicios Docker (`api` y `web`) más un PostgreSQL administrado. La configuración de producción va en las variables del proveedor. |

---

## Pendientes y observaciones técnicas del módulo de auth

- **Restablecer la contraseña:** fuera de alcance por decisión del equipo. Falta el endpoint que
  consuma `password_reset_token` (validar hash, vencimiento y `used_at`, y actualizar
  `password_hash`).
- **RF-01.4 · Editar perfil:** no hay endpoint.
- **Rotación de refresh tokens:** el silent refresh no emite un refresh token nuevo, así que el
  mismo token sirve durante 14 días.
- **Access token vencido:** si el cliente envía un access token vencido, `verify-session`
  responde `401` sin intentar usar la cookie de refresh. El frontend lo resuelve llamando sin el
  header `Authorization` (`renovarSesion()` en `src/services/client.js`).
- **Limpieza de tokens:** las filas vencidas o revocadas de `refresh_token` y
  `password_reset_token` no se eliminan nunca.
- **Zona horaria en `revoke`:** `SQLAlchemyRefreshTokenRepository.revoke` usa `datetime.now()`
  sin zona horaria, aunque la columna es `timezone=True`.
- **Rate limiting en memoria:** `InMemoryLoginAttemptsStore` no comparte estado entre workers.
- **Emails:** `ConsoleEmailSender` no envía emails reales. La URL base del link de reset está
  hardcodeada (`TODO: mover a Settings`).
