# Estado de implementación

## Plataforma de descubrimiento de eventos por geolocalización

**Fecha de relevamiento:** 15/10/2026 · **Commit de referencia:** `85e3eb5` (merge PR #5, `refactor/registro`)

---

## Resumen

Hasta el momento solo está implementado el **módulo de autenticación del backend**
(`backend/app/auth`, FastAPI + SQLAlchemy + PostgreSQL). Todavía no hay frontend ni módulos de
eventos, categorías, organizadores o moderación. La única migración (`0001_auth_tables`) crea las
tablas `usuario`, `refresh_token`, `password_reset_token` y `audit_log`.

| Ítem | Estado |
|---|---|
| Requisitos funcionales **Must** implementados | 2 de 26 (RF-01.1 y RF-01.3) |
| Requisitos funcionales con avance parcial | RF-01.5 (solo preparación del diseño) |
| Casos de uso documentados (CU-01 a CU-04) implementados | 0 de 4 |
| Tests automatizados | 41 funciones de test en `backend/tests/auth` |

---

## Requisitos funcionales

### Implementados

| # | Requisito | Prioridad | Implementación |
|---|---|---|---|
| RF-01.1 | Registrar un usuario con nombre, apellido, email y contraseña | **M** | `POST /auth/register` → `EmailRegister`. Valida email, contraseña de 8 a 128 caracteres y nombre/apellido obligatorios. Rechaza emails duplicados (409). No inicia sesión automáticamente. |
| RF-01.3 | Iniciar y cerrar sesión mediante email y contraseña | **M** | `POST /auth/login` → `EmailSignIn` (envuelto en `RateLimitedSignIn`). Devuelve un access token JWT y deja un refresh token en una cookie `httpOnly`. `POST /auth/logout` revoca el refresh token y borra la cookie. `POST /auth/verify-session` permite mantener la sesión (silent refresh). |

### Parcialmente preparados

| # | Requisito | Prioridad | Estado |
|---|---|---|---|
| RF-01.5 | Autenticación mediante proveedores externos (login social) | **C** | **No implementado**, aunque el diseño lo contempla: `password_hash` es nullable, `Auth` se arma con estrategias intercambiables (Strategy) y existe `UnsupportedRecovery` (Null Object) para proveedores sin contraseña local. No hay endpoints ni integración con Google/Facebook. |
| RF-03.8 | Uso pleno sin permiso de geolocalización (ubicación por defecto + buscador de lugar) | **M** | **Backend listo, falta el frontend.** `GET /config/ubicacion-default` (público) devuelve `nombre`, `lat`, `lng` y `zoom`, configurables con `UBICACION_DEFAULT_*` y validados al arrancar. El buscador de lugar es `GET /geocodificacion/buscar`. |
| RF-03.10 | Ficha de detalle del evento con los datos del organizador | **M** | **Backend listo, falta el frontend.** `GET /eventos/{id_evento}` (requiere login) devuelve el evento y un bloque `organizador` con `id_organizador`, `nombre_publico` y `descripcion` (sin `id_usuario` ni estado del perfil). Un evento de seed trae `{"id_organizador": null, "nombre_publico": "Equipo de la plataforma", ...}`. Visibilidad: PUBLICADO y CANCELADO los ve cualquiera, aunque ya hayan terminado (responde la pregunta abierta #4 de `planning.md`: la búsqueda los oculta, la URL directa no); BORRADOR solo su organizador; OCULTO nadie. Si no se puede ver, 404. |

### Pendientes

| Grupo | Requisitos |
|---|---|
| RF-01 · Cuentas | RF-01.2 (descubrir eventos: depende de RF-03), RF-01.4 (editar perfil), RF-01.6 (solicitud de organizador), RF-01.7 (restricción de alta de eventos a organizadores), RF-01.8 |
| RF-02 · Gestión de eventos | RF-02.1 a RF-02.10 |
| RF-03 · Descubrimiento y búsqueda | RF-03.1 a RF-03.14 (RF-03.8 y RF-03.10 con avance parcial, ver abajo) |
| RF-04 · Categorías | RF-04.1 a RF-04.3 |
| RF-05 · Moderación | RF-05.1 a RF-05.5 |
| RF-06 · Ingesta externa | RF-06.1 |
| RF-07 · Monetización | RF-07.1, RF-07.2 |

### Funcionalidad implementada que no figura como RF

| Funcionalidad | Detalle |
|---|---|
| Solicitud de recuperación de contraseña | `POST /auth/recover-password` → `EmailRecovery`. Genera un token de un solo uso (60 min), guarda su hash en `password_reset_token` y envía el link por email. **Falta el paso de consumirlo** (no hay un endpoint que valide el token y cambie la contraseña, y `used_at` nunca se escribe). |
| Registro de auditoría | `AuditLogObserver` escribe en `audit_log` los 5 eventos de auth: `user_registered`, `login_succeeded`, `login_failed`, `password_recovery_requested` y `session_verified`. |
| Emails transaccionales | `EmailNotificationObserver` envía un email de bienvenida al registrarse y el link de recuperación. Hoy usa `ConsoleEmailSender`, que solo los escribe en el log. |

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
| RNF-05.3 | FastAPI + OpenAPI + Pydantic | Schemas Pydantic en `app/auth/schemas.py` |

---

## Casos de uso

### Casos de uso documentados (`04-casos-de-uso.md`)

| Caso de uso | Estado | Observación |
|---|---|---|
| CU-01 · Usuario descubre eventos cerca de su ubicación actual | ❌ No implementado | Requiere el modelo de eventos, la búsqueda por viewport y el frontend con mapa. Para el flujo 3a (permiso rechazado), el backend ya expone la ubicación por defecto en `GET /config/ubicacion-default` |
| CU-02 · Usuario explora eventos en una ubicación distinta | 🟡 Parcial (backend) | Pasos 2 y 2a: `GET /geocodificacion/buscar?q=` consulta Nominatim y devuelve sugerencias con su bounding box (`lat_min`/`lat_max`/`lng_min`/`lng_max`, los mismos nombres que el viewport de `GET /eventos`). Sin coincidencias → `[]`; Nominatim caído → `503`. Falta el buscador en el frontend |
| CU-03 · Organizador publica un nuevo evento | ❌ No implementado | Requiere el perfil de organizador y el modelo de eventos |
| CU-04 · Usuario solicita convertirse en organizador | ❌ No implementado | Su precondición ("tiene una cuenta registrada e inició sesión") **ya está cubierta** por el módulo de auth |

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
- **Rol de administrador (RNF-04.4):** todavía sin definir. Es un prerrequisito de RF-05.
