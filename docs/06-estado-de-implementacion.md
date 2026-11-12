# Estado de implementación

## Plataforma de descubrimiento de eventos por geolocalización

**Fecha de relevamiento:** 04/11/2026 · **Rama:** `guille/must-pendientes` (alta de eventos, sobre `f19e0d7`, merge del PR #11)

---

## Resumen

Está implementado solo el **backend** (FastAPI + SQLAlchemy + PostgreSQL), con los módulos de
autenticación (`auth`), organizadores y administradores (solicitud, aprobación, rechazo y
suspensión de organizadores), categorías, eventos (búsqueda por viewport, ficha de detalle, mis
eventos, alta, edición, cancelación y ocultamiento por un administrador), geocodificación (búsqueda de
lugares en Nominatim) y configuración (ubicación por defecto), más un script de seed de eventos.
Todavía no hay frontend, así que los requisitos de descubrimiento (RF-03) están cubiertos solo del
lado de la API. Hay 4 migraciones (`0001_auth_tables` a `0004_eventos`).

| Ítem | Estado |
|---|---|
| Requisitos funcionales **Must** implementados | 22 de 23 (ver `02-requisitos-funcionales.md`). RF-03.3, RF-03.7, RF-03.8 y RF-03.10 solo en el backend. El único pendiente, RF-03.1, es de frontend |
| Requisitos funcionales con avance parcial | RF-01.5 (solo preparación del diseño) |
| Casos de uso documentados (CU-01 a CU-04) implementados | 0 de 4 (CU-03 y CU-04 con el backend completo, CU-02 parcial en el backend) |
| Tests automatizados | 233 funciones de test en `backend/tests` |

---

## Requisitos funcionales

### Implementados

| # | Requisito | Prioridad | Implementación |
|---|---|---|---|
| RF-01.1 | Registrar un usuario con nombre, apellido, email y contraseña | **M** | `POST /auth/register` → `EmailRegister`. Valida email, contraseña de 8 a 128 caracteres y nombre/apellido obligatorios. Rechaza emails duplicados (409). No inicia sesión automáticamente. |
| RF-01.3 | Iniciar y cerrar sesión mediante email y contraseña | **M** | `POST /auth/login` → `EmailSignIn` (envuelto en `RateLimitedSignIn`). Devuelve un access token JWT y deja un refresh token en una cookie `httpOnly`. `POST /auth/logout` revoca el refresh token y borra la cookie. `POST /auth/verify-session` permite mantener la sesión (silent refresh). |
| RF-01.2 | Todo usuario registrado puede descubrir eventos | **M** | `GET /eventos` y `GET /eventos/{id_evento}` piden login (`get_usuario_actual`) pero ningún rol: cualquier usuario registrado puede buscar eventos y ver su ficha, sea organizador o no. Sin sesión → `401`. |
| RF-01.6 | Solicitar convertirse en organizador (nombre público y descripción), queda `PENDIENTE` | **M** | `POST /organizadores/solicitud` → `SolicitarOrganizador` (requiere login). Crea el perfil en `PENDIENTE`. Un usuario tiene como mucho un perfil (`id_usuario` UNIQUE): con una solicitud pendiente o aprobada responde `409`, y si está suspendido, `403`. Un rechazado puede volver a solicitar y se reutiliza la misma fila (flujo 5a de CU-04). |
| RF-01.7 | Crear y editar eventos solo con perfil de organizador `APROBADO` | **M** | La dependencia `require_organizador_aprobado` responde `403` si el usuario no tiene perfil de organizador o si su perfil no está `APROBADO` (pendiente, rechazado o suspendido). Protege `POST /eventos`, `GET /eventos/mios`, `PATCH /eventos/{id_evento}` y `POST /eventos/{id_evento}/cancelar`. El estado se consulta en la base en cada request, así que una suspensión corta el acceso de inmediato. |
| RF-02.1 | Alta de un evento con título, descripción, inicio, fin (opcional) y precio (opcional) | **M** | `POST /eventos` → `CrearEvento` (CU-03). El evento queda `PUBLICADO`, con `origen = CARGA_ORGANIZADOR`, asociado al organizador y con `fecha_publicacion`; responde `201` y aparece en "mis eventos". Las fechas deben tener zona horaria; `fecha_fin` tiene que ser posterior al inicio y el inicio tiene que ser futuro; el precio no puede ser negativo. Cualquier dato inválido responde `422`. |
| RF-02.2 | Ubicar el evento marcando un punto en el mapa (coordenadas como dato autoritativo) | **M** | `lugar` es obligatorio en el alta, con `latitud` (-90 a 90) y `longitud` (-180 a 180); `nombre` y `direccion` son opcionales y descriptivos. Cada alta crea su propio `Lugar`. Marcar el punto en un mapa es responsabilidad del frontend. |
| RF-02.3 | Asociar el evento a una o varias categorías del catálogo | **M** | `categorias` recibe al menos un slug. Se validan contra el catálogo activo con la misma regla que la edición: un slug inexistente o inactivo responde `422`, y los repetidos se ignoran. |
| RF-02.4 | Editar y dar de baja (cancelar) un evento propio | **M** | `PATCH /eventos/{id_evento}` → `EditarEvento`: edición parcial (solo los campos enviados), `lugar` y `categorias` reemplazan la lista completa, las categorías se validan contra el catálogo activo y `fecha_fin` debe ser posterior al inicio (si no, `422`). Solo se editan eventos `BORRADOR` o `PUBLICADO` (si no, `409`). `POST /eventos/{id_evento}/cancelar` → `CancelarEvento`, válido desde `BORRADOR` o `PUBLICADO`. Ambos exigen ser el organizador dueño (si no, `403`). |
| RF-02.5 | Listado de "mis eventos" con su estado actual | **M** | `GET /eventos/mios` → `ListarMisEventos`: todos los eventos del organizador, en cualquier estado (incluidos los cancelados y ocultos). |
| RF-03.2 | Vista de lista con los mismos resultados que la vista mapa | **M** | Mapa y lista consumen el mismo `GET /eventos`, que devuelve una página (`items`, `total`, `limit`, `offset`; 20 por defecto, máximo 100) con orden estable por inicio e id. Hay tests de que los mismos parámetros dan siempre el mismo orden y de que recorrer las páginas no repite ni pierde eventos. |
| RF-03.4 | Filtrar por rango de fechas | **M** | `GET /eventos?desde=&hasta=` (fechas locales, extremos inclusivos, se filtra por el inicio del evento). Cada límite se convierte a UTC con `Settings.zona_horaria`. `desde` posterior a `hasta` → `422`. |
| RF-03.5 | Filtrar por rango horario | **M** | `GET /eventos?hora_desde=&hora_hasta=` (HH:MM, extremos inclusivos) contra `hora_inicio_local`. Si `hora_desde` es posterior a `hora_hasta`, el rango cruza la medianoche (22:00 a 02:00). |
| RF-03.6 | Filtrar por una o varias categorías | **M** | `GET /eventos?categorias=bar&categorias=teatro`: coincide un evento con al menos una de las categorías pedidas. Se resuelve con una subconsulta para no duplicar eventos con varias categorías ni romper la paginación. |
| RF-04.1 | Catálogo cerrado de categorías | **M** | La migración `0004_eventos` carga las 11 categorías en `categoria_evento`. `GET /categorias` (público) lista las activas. La API no permite crear categorías. |
| RF-04.2 | Asociar múltiples categorías a un evento | **M** | Asociación N:M mediante la tabla `evento_categoria`. Al crear y al editar, `categorias` recibe una lista de slugs (al menos uno). |
| RF-05.1 | Un administrador oculta cualquier evento publicado | **M** | `POST /admin/eventos/{id_evento}/ocultar` → `OcultarEvento` (requiere administrador). Válido desde `PUBLICADO` o `CANCELADO` (si no, `409`). Un evento `OCULTO` desaparece de la búsqueda y de la ficha de detalle; su dueño lo sigue viendo en "mis eventos". |
| RF-05.2 | Eventos de origen propio (seed) diferenciados | **M** | `Evento.origen` distingue `SEED_EQUIPO` de `CARGA_ORGANIZADOR`. `scripts/seed.py` carga eventos de ejemplo sin organizador mediante `EventoFactory.crear_seed`, repartidos en distintas zonas, fechas, horarios y categorías (`--reset` borra el seed y lo recarga). |
| RF-05.5 | Un administrador aprueba, rechaza y suspende perfiles de organizador | **S** | `GET /admin/organizadores?estado=` lista los perfiles en un estado. `POST /admin/organizadores/{id}/aprobar` y `/rechazar` son válidos desde `PENDIENTE`; `/suspender`, desde `APROBADO`. Una transición inválida responde `409`. |

### Parcialmente preparados

| # | Requisito | Prioridad | Estado |
|---|---|---|---|
| RF-01.5 | Autenticación mediante proveedores externos (login social) | **C** | **No implementado**, aunque el diseño lo contempla: `password_hash` es nullable, `Auth` se arma con estrategias intercambiables (Strategy) y existe `UnsupportedRecovery` (Null Object) para proveedores sin contraseña local. No hay endpoints ni integración con Google/Facebook. |
| RF-03.3 | Desplazar y hacer zoom sobre el mapa, re-ejecutando la búsqueda según el viewport | **M** | **Backend listo, falta el frontend.** `GET /eventos` acepta `lat_min`, `lat_max`, `lng_min` y `lng_max` (filtro `filtrar_por_viewport`, bordes inclusivos). Vienen los cuatro o ninguno y el mínimo no puede superar al máximo, así que no se admiten viewports que crucen el antimeridiano; si no, `422`. Sin viewport no filtra. Falta el mapa que vuelva a llamar al endpoint al desplazarse o hacer zoom. |
| RF-03.7 | Buscar y establecer una ubicación de referencia distinta a la actual | **M** | **Backend listo, falta el frontend.** `GET /geocodificacion/buscar?q=` (requiere login) consulta Nominatim y devuelve sugerencias con su bounding box (`lat_min`/`lat_max`/`lng_min`/`lng_max`, los mismos nombres que el viewport de `GET /eventos`), así una sugerencia elegida se puede pasar directo a la búsqueda. Sin coincidencias → `[]`; Nominatim caído → `503`. Fijar la ubicación de referencia y centrar el mapa es responsabilidad del frontend. |
| RF-03.8 | Uso pleno sin permiso de geolocalización (ubicación por defecto + buscador de lugar) | **M** | **Backend listo, falta el frontend.** `GET /config/ubicacion-default` (público) devuelve `nombre`, `lat`, `lng` y `zoom`, configurables con `UBICACION_DEFAULT_*` y validados al arrancar. El buscador de lugar es `GET /geocodificacion/buscar`. |
| RF-03.10 | Ficha de detalle del evento con los datos del organizador | **M** | **Backend listo, falta el frontend.** `GET /eventos/{id_evento}` (requiere login) devuelve el evento y un bloque `organizador` con `id_organizador`, `nombre_publico` y `descripcion` (sin `id_usuario` ni estado del perfil). Un evento de seed trae `{"id_organizador": null, "nombre_publico": "Equipo de la plataforma", ...}`. Visibilidad: PUBLICADO y CANCELADO los ve cualquiera, aunque ya hayan terminado (responde la pregunta abierta #4 de `planning.md`: la búsqueda los oculta, la URL directa no); BORRADOR solo su organizador; OCULTO nadie. Si no se puede ver, 404. |

### Pendientes

| Grupo | Requisitos |
|---|---|
| RF-01 · Cuentas | RF-01.4 (editar perfil), RF-01.8 |
| RF-02 · Gestión de eventos | RF-02.6 a RF-02.10 |
| RF-03 · Descubrimiento y búsqueda | RF-03.1 (solo frontend: el backend que necesita, viewport y ubicación por defecto, ya está), RF-03.9, RF-03.11 a RF-03.14 (RF-03.3, RF-03.7, RF-03.8 y RF-03.10 tienen el backend listo, ver arriba) |
| RF-04 · Categorías | RF-04.3 (el modelo ya tiene `activa` para retirar una categoría sin borrarla, pero no hay endpoints de administración) |
| RF-05 · Moderación | RF-05.3, RF-05.4 |
| RF-06 · Ingesta externa | RF-06.1 |
| RF-07 · Monetización | RF-07.1, RF-07.2 |

### Funcionalidad implementada que no figura como RF

| Funcionalidad | Detalle |
|---|---|
| Solicitud de recuperación de contraseña | `POST /auth/recover-password` → `EmailRecovery`. Genera un token de un solo uso (60 min), guarda su hash en `password_reset_token` y envía el link por email. **Falta el paso de consumirlo** (no hay un endpoint que valide el token y cambie la contraseña, y `used_at` nunca se escribe). |
| Registro de auditoría | `AuditLogObserver` escribe en `audit_log` los 5 eventos de auth: `user_registered`, `login_succeeded`, `login_failed`, `password_recovery_requested` y `session_verified`. |
| Emails transaccionales | `EmailNotificationObserver` envía un email de bienvenida al registrarse y el link de recuperación. Hoy usa `ConsoleEmailSender`, que solo los escribe en el log. |
| Usuario actual con sus roles | `GET /auth/me` (`app/perfil/router.py`): datos del usuario autenticado, su perfil de organizador (`id_organizador`, `nombre_publico`, `estado`) o `null`, y `es_admin`. Lo usa el frontend después del login y al restaurar la sesión para mostrar u ocultar las acciones de organizador y de administrador. Sin token `401`, cuenta inactiva `403`. |
| Errores de validación en español | `app/core/validation_errors.py`: handler de `RequestValidationError` que traduce el `msg` de cada error según su `type` de Pydantic y mantiene el formato `{"detail": [{loc, msg, type}]}`. Los validadores propios conservan su texto y un tipo sin traducción conserva el mensaje original. No devuelve `input` ni `ctx`. |

---

## Requisitos no funcionales cubiertos

| # | Requisito | Cómo se cubre |
|---|---|---|
| RNF-04.1 | Contraseñas con hashing seguro | `Argon2PasswordHasher` (argon2) |
| RNF-04.2 | Autenticación por JWT, access token en memoria del cliente | El access token viaja en el cuerpo de la respuesta y el refresh token en una cookie `httpOnly` con path `/auth`. Que el cliente lo guarde solo en memoria es responsabilidad del frontend, que todavía no existe. |
| RNF-04.3 | Identificadores no secuenciales (UUID) | PK UUID en las 4 tablas |
| RNF-04 (general) | Mitigación de fuerza bruta y enumeración | Bloqueo tras 5 intentos fallidos en 15 min (`RateLimitedSignIn`, devuelve 423). Respuestas idénticas en la recuperación de contraseña, exista o no el email. |
| RNF-01.4 | Caché local de las búsquedas de lugares | `CachedGeocodificador` (Decorator, `app/geocodificacion/decorators/cached.py`): caché en memoria por proceso, con TTL y tope de entradas configurables (`GEOCODIFICACION_CACHE_TTL_SEGUNDOS`, `GEOCODIFICACION_CACHE_MAX_ENTRADAS`). No cachea errores. |
| RNF-05.1 | Política de uso de Nominatim | `RateLimitedGeocodificador` (Decorator) espacia las requests salientes a ≥1 s (las que llegan antes esperan, no se rechazan); `User-Agent` configurable en `Settings.nominatim_user_agent`. `GET /geocodificacion/buscar` requiere login, así la API no queda como proxy anónimo. Límite conocido: el estado es por proceso (un único worker). |
| RNF-05.2 | PostgreSQL en dev/prod, SQLite solo en tests | `database_url` por defecto en PostgreSQL. Los tests usan `aiosqlite`. |
| RNF-04.4 | Moderación restringida a administradores | Tabla `administradores` (migración `0003_administradores`): un usuario es administrador si tiene una fila ahí, y `Usuario` sigue sin rol. `get_admin_actual` protege todo `/admin/...`: sin sesión `401`, sin perfil de administrador `403`. No hay endpoint para dar de alta administradores; se cargan directo en la base. |
| RNF-05.3 | FastAPI + OpenAPI + Pydantic | Schemas Pydantic en `app/auth/schemas.py` |

---

## Casos de uso

### Casos de uso documentados (`04-casos-de-uso.md`)

| Caso de uso | Estado | Observación |
|---|---|---|
| CU-01 · Usuario descubre eventos cerca de su ubicación actual | ❌ No implementado | Requiere el modelo de eventos, la búsqueda por viewport y el frontend con mapa. Para el flujo 3a (permiso rechazado), el backend ya expone la ubicación por defecto en `GET /config/ubicacion-default` |
| CU-02 · Usuario explora eventos en una ubicación distinta | 🟡 Parcial (backend) | Pasos 2 y 2a: `GET /geocodificacion/buscar?q=` consulta Nominatim y devuelve sugerencias con su bounding box (`lat_min`/`lat_max`/`lng_min`/`lng_max`, los mismos nombres que el viewport de `GET /eventos`). Sin coincidencias → `[]`; Nominatim caído → `503`. Falta el buscador en el frontend |
| CU-03 · Organizador publica un nuevo evento | 🟡 Backend listo | Pasos 7 a 9: `POST /eventos` valida los datos, guarda el evento `PUBLICADO` asociado al organizador y el evento aparece en `GET /eventos/mios`. Flujo 8a: datos faltantes o inválidos (incluida una fecha de fin anterior al inicio o un inicio que ya pasó) → `422`. Flujos 9a y 9b: `PATCH /eventos/{id_evento}` y `POST /eventos/{id_evento}/cancelar`. Faltan el formulario y el mapa para marcar el pin (pasos 1 a 6) |
| CU-04 · Usuario solicita convertirse en organizador | 🟡 Backend listo | Paso 4: `POST /organizadores/solicitud` crea el perfil en `PENDIENTE`. Pasos 5 y 6 y flujo 5a: el administrador lista las solicitudes con `GET /admin/organizadores?estado=PENDIENTE` y las aprueba o rechaza; un rechazado puede volver a solicitar. Faltan el formulario, el panel de administración y avisarle al usuario el resultado (no se manda email) |

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
- **Pendiente:** el endpoint para restablecer la contraseña con el token.

---

## Pendientes y observaciones técnicas del módulo de auth

- **Restablecer la contraseña:** falta el endpoint que consuma `password_reset_token` (validar
  hash, vencimiento y `used_at`, y actualizar `password_hash`).
- **RF-01.4 · Editar perfil:** no hay endpoint.
- **Rotación de refresh tokens:** el silent refresh no emite un refresh token nuevo, así que el
  mismo token sirve durante 14 días.
- **Access token vencido:** si el cliente envía un access token vencido, `verify-session`
  responde `401` sin intentar usar la cookie de refresh. El frontend debe llamar sin el header
  `Authorization` para renovar la sesión.
- **Limpieza de tokens:** las filas vencidas o revocadas de `refresh_token` y
  `password_reset_token` no se eliminan nunca.
- **Zona horaria en `revoke`:** `SQLAlchemyRefreshTokenRepository.revoke` usa `datetime.now()`
  sin zona horaria, aunque la columna es `timezone=True`.
- **Rate limiting en memoria:** `InMemoryLoginAttemptsStore` no comparte estado entre workers.
- **Emails:** `ConsoleEmailSender` no envía emails reales. La URL base del link de reset está
  hardcodeada (`TODO: mover a Settings`).
