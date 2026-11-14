# Pendientes para el deploy en producción

**Relevamiento:** 14/11/2026 · **Base:** `main` en `9ccb8da` (merge del PR #17, Docker + CI)

Estado de partida: los 23 requisitos Must están implementados (backend y frontend), el backend pasa
340 tests con 95% de cobertura y el frontend pasa lint y build. Lo que falta es **infraestructura y
configuración de producción**, no funcionalidad.

> Archivo de trabajo, sin trackear en git. Marcar cada ítem con `[x]` a medida que se resuelve.

---

## Bloqueantes (sin esto no se puede deployar)

### B-1 · Despliegue del frontend y mismo dominio que la API
> **Implementado y verificado en local (14/11/2026); falta verificar en el PaaS.** Destino: PaaS (Render, Railway o Fly) con dos servicios
> Docker, `web` (nginx) y `api`. Ver la sección "Deploy en un PaaS" del README.

- [x] Crear `frontend/Dockerfile`: multi-stage, build con `node:22-alpine` y servido con `nginx:1.27-alpine`.
- [x] Proxy inverso en `frontend/nginx/default.conf.template`: sirve el frontend en `/` y reenvía
      `/api/*` a `${API_UPSTREAM}` **sacando el prefijo**, igual que el proxy de Vite.
- [x] Reescritura del path de la cookie con `proxy_cookie_path /auth /api/auth;`.
- [x] `VITE_API_URL` sin definir en el build, así queda el default `/api`
      (`frontend/src/services/client.js:5`).
- [x] Fallback de la SPA para rutas profundas (`try_files $uri $uri/ /index.html`).
- [x] Servicio `web` en `compose.yaml` (`http://localhost:8080`).
- [x] La API escucha en `${PORT:-8000}`, con `--proxy-headers` (`backend/Dockerfile`).
- [x] Verificado en local con `docker compose up -d --build` sobre `http://localhost:8080`: las
      imágenes construyen, la SPA y las rutas profundas devuelven `index.html`, `/api/*` llega a la
      API, el login setea `refresh_token` con `Path=/api/auth`, `verify-session` renueva la sesión
      solo con la cookie (es lo que pasa al recargar la página), y el logout la borra.
      En esta máquina el puerto 5432 está ocupado; ver B-3 sobre no publicarlo.
- [x] **Resolución DNS del upstream:** nginx resolvía el host de `API_UPSTREAM` una sola vez, al
      arrancar, y con un redeploy de la API que le cambiara la IP, `web` respondía `502` hasta
      reiniciarse (reproducido en local). Arreglado con `resolver` (DNS del contenedor vía
      `NGINX_ENTRYPOINT_LOCAL_RESOLVERS=1`, `valid=10s`) y `proxy_pass` con variable + `rewrite`
      para sacar el prefijo. Verificado: después del cambio de IP nginx sigue a la API nueva y la
      query string llega intacta.
- [ ] Verificar en el PaaS: lo mismo sobre la URL https de `web`, más la geolocalización del mapa.

**Por qué bloquea:** la cookie del refresh es `SameSite=lax`; si front y API quedan en dominios
distintos o el path no coincide, la sesión no se renueva y el usuario queda deslogueado a los 15 minutos.

### B-2 · CORS configurable
- [ ] Mover `allow_origins` (hoy fijo en `http://localhost:5173`, `backend/app/main.py:65`) a
      `Settings` (por ejemplo `CORS_ORIGINS`, lista separada por comas) y documentarlo en `.env.example`.

**Ya no bloquea:** con B-1 el navegador le habla solo a nginx, en el mismo origen, así que CORS no
interviene. Queda como limpieza: no debería quedar el origen de desarrollo fijo en el código.

### B-3 · Secretos y configuración de producción
> **Resuelto en código (14/11/2026), sin commitear.** Con el destino en un PaaS, la configuración
> de producción vive en las variables del proveedor, así que no hace falta un `compose.prod.yaml`.

- [x] La API **no arranca** si `JWT_SECRET_KEY` falta, tiene menos de 32 caracteres o es uno de los
      valores de ejemplo del repo (`field_validator` en `backend/app/core/config.py`). Verificado
      con `docker run` sin la variable y con el valor de `.env.example`.
- [x] `hide_input_in_errors=True` en `Settings`: un valor inválido (secreto, `DATABASE_URL` con
      contraseña) no se imprime en los logs del arranque.
- [x] Tests: `backend/tests/core/test_settings_jwt_secret.py`. `tests/conftest.py` define un
      secreto de tests, así que la CI (sin `.env`) sigue andando: 347 tests verificados sin `.env`.
- [x] `compose.yaml` queda explícitamente para desarrollo (documentado en el README): sus
      secretos de desarrollo no se usan en producción.
  - [x] Puerto de Postgres atado a `127.0.0.1` y configurable con `DB_PUERTO_HOST` (en esta
        máquina el 5432 está ocupado: `DB_PUERTO_HOST=5433 docker compose up -d`).
  - [x] `COOKIE_SECURE=true` en producción: es el default de `Settings`. Solo el compose de
        desarrollo lo pone en `false`.
  - [x] Política de reinicio: la maneja el PaaS.
- [ ] HTTPS: lo da el PaaS. Confirmarlo en el primer deploy.
- [ ] Generar la `JWT_SECRET_KEY` de producción y cargarla en el proveedor; tiene que ser distinta
      de la del `.env` local.

### B-4 · Builds reproducibles de la imagen del backend
> **Resuelto en código (14/11/2026), sin commitear.**

- [x] `backend/Dockerfile` multi-stage: una primera etapa con Poetry 2.5.1 (la que generó el lock)
      y `poetry-plugin-export` exporta las dependencias `main` a un `requirements.txt` con
      versiones exactas y hashes. La imagen final instala ese archivo con pip y no lleva Poetry.
      Si el lock queda desactualizado respecto de `pyproject.toml`, el build falla.
      Verificado: fastapi, sqlalchemy, pydantic, asyncpg y uvicorn tienen en la imagen las mismas
      versiones que en `poetry.lock`.
- [x] Construir la imagen al menos una vez y verificar que arranca: verificado el 14/11/2026 con
      `docker compose up --build` (corre las migraciones en Postgres y la API responde vía nginx).

### B-5 · Requisitos operativos de servicios externos y datos iniciales
- [ ] Definir `NOMINATIM_USER_AGENT` con un contacto real del equipo (email o URL). La política de
      uso de Nominatim lo exige y puede bloquear a la app si no.
- [x] Alta de administradores: **decisión del equipo, se asignan a mano en la base** (no hay endpoint
      ni script, a propósito). Documentado en el README ("Alta de administradores", con la consulta
      para quitar el rol). Pasos:
      1. La persona se registra desde la app (así su contraseña queda hasheada con Argon2).
      2. Desde la consola SQL del proveedor (o `psql` con la URL de la base):
         ```sql
         INSERT INTO administradores (id_usuario)
         SELECT id_usuario FROM usuario WHERE email = '<email>'
         ON CONFLICT (id_usuario) DO NOTHING;
         ```
         `id_admin` lo genera la base (`DEFAULT gen_random_uuid()`, migración
         `0005_administradores_id_default`, rama `franco/admin-id-default`). `ON CONFLICT` hace que
         repetirlo no falle. Si responde `INSERT 0 0` en el primer intento, el email no está
         registrado. **Hasta aplicar la 0005 en Supabase, ahí hay que seguir pasando `id_admin`.**
      3. La persona vuelve a ingresar (o recarga) y le aparece "Administración" en la barra: el
         permiso se consulta en la base en cada request.
      Verificado en el Postgres local del compose (14/11/2026).
- [ ] Decidir si en producción se corre `scripts.seed` (eventos del equipo, RF-05.2).

---

## Importantes (resolver antes o inmediatamente después del primer deploy)

### I-1 · El CI no valida la imagen Docker
- [x] Job "Imagenes Docker" en `.github/workflows/pipeline.yaml`: construye las dos imágenes con
      `docker compose up -d --build` y prueba la app a través de nginx (API en `/api`, SPA en una
      ruta profunda, cookie del login con `Path=/api/auth`). Comandos probados en local; falta verlo
      correr en GitHub Actions al subir la rama.

### I-2 · Recuperación de contraseña a medias

> **Fuera de alcance por decisión del equipo (14/11/2026).** No bloquea el deploy: el frontend no
> tiene ninguna pantalla ni enlace de recuperación, así que no hay nada que ocultar. Solo queda
> expuesto `POST /auth/recover-password` en la API, que genera un token que nada consume.

- [ ] `ConsoleEmailSender` solo imprime los emails en el log: implementar un sender real (SMTP o un
      proveedor), configurable desde `Settings`.
- [ ] El link de reset apunta a `https://app.example.com/reset-password`
      (`backend/app/auth/events/observers/email_notification_observer.py:12`, `TODO: mover a Settings`).
- [ ] Falta el endpoint que consume el token (`password_reset_token`: validar hash, vencimiento y
      `used_at`, y actualizar `password_hash`) y la página del frontend.
- **Mínimo aceptable para el deploy:** ocultar la opción de recuperar la contraseña hasta completarla.

### I-3 · Tests del frontend (etapa 5, paso 1 de la hoja de ruta)

> **Fuera de alcance por decisión del equipo (14/11/2026).**

- [ ] Vitest + Testing Library para `useFormSubmit`, `useBusquedaEventos`, `useUbicacionInicial` y
      los formularios, y sumarlos al pipeline.

### I-4 · Documentación
- [x] `docs/06-estado-de-implementacion.md` actualizado al 14/11/2026 (frontend, infraestructura y
      decisiones de alcance). También se cerró la etapa 5 en `docs/08-hoja-de-ruta-frontend.md`.
- [x] README con la sección "Arquitectura del frontend" y el procedimiento de deploy ("Deploy en un
      PaaS" y "Alta de administradores").

---

## Menores (deuda técnica, no bloquean)

- [ ] El contenedor de la API corre como `root`: agregar un usuario sin privilegios en el `Dockerfile`.
- [ ] Health check que verifique la conexión a la base (hoy `/` responde siempre `"Hola mundo"`) y
      usarlo en el `healthcheck` del servicio `api`.
- [ ] `SQLAlchemyRefreshTokenRepository.revoke` usa `datetime.now()` sin zona horaria
      (`backend/app/auth/token_repository.py:45`) sobre una columna `timezone=True`.
- [ ] El refresh token no rota: el mismo sirve durante 14 días.
- [ ] Rate limiting de login en memoria (`InMemoryLoginAttemptsStore`): se pierde en cada reinicio y
      no se comparte si se escala a varios workers. Mantener 1 worker o moverlo a la base/Redis.
- [ ] Los tokens vencidos o revocados (`refresh_token`, `password_reset_token`) nunca se borran.
- [ ] `sqladmin` está en las dependencias pero no se usa.
- [ ] El bundle del frontend pesa 523 kB: code splitting por ruta con `import()` dinámico.
- [ ] Warning de oxlint en `frontend/src/features/auth/context/AuthContext.jsx:69`
      (`only-export-components`).

---

## Checklist de salida

- [ ] B-1 a B-5 resueltos.
- [x] I-2 resuelto o la recuperación de contraseña oculta: el frontend no la ofrece (I-2 queda fuera de alcance).
- [ ] Deploy de prueba en un entorno de staging: registro → login → explorar mapa → solicitud de
      organizador → aprobación por un administrador → alta de evento → el evento aparece en el mapa.
- [ ] Recargar la página después de 15 minutos sigue con la sesión iniciada (verifica la cookie, B-1).
