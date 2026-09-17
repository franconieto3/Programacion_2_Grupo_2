# Plan de producto y arquitectura — Plataforma de descubrimiento de eventos por geolocalización

## Contexto

El problema que motiva el producto: la oferta de actividades de una zona está fragmentada entre
los canales de cada organizador (redes del bar, del teatro, de la banda, de la marca). Si no
seguís a quien organiza, no te enterás. La hipótesis es que centralizar esa oferta y hacerla
navegable **por ubicación, fecha y categoría** — en vez de por organizador — resuelve tanto el
caso "qué hago hoy acá" como el caso "qué voy a hacer en Mar del Plata la semana que viene".

Este plan cubre un entregable con doble naturaleza, definida por vos en la sesión de planning:
es el **trabajo práctico de Programación 2** (equipo de 3-5 personas, pocas semanas, con CI/CD y
control de versiones como criterio de evaluación explícito) y a la vez la **base de un producto
real a futuro**. Esa dualidad es la que gobierna casi todas las decisiones de abajo: se prioriza
lo que se puede terminar y defender en el plazo, sin cerrar puertas arquitectónicas que después
obliguen a reescribir.

Repositorio: `franconieto3/Programacion_2_Grupo_2` — hoy vacío (solo `README.md`, 1 commit).
No hay código heredado ni restricciones previas.

---

## 1. Decisiones ya tomadas (cerradas en el planning)

| Tema | Decisión |
|---|---|
| Naturaleza | TP ahora, producto después → arquitectura desacoplada (API + SPA) |
| Restricción de stack | Backend en Python obligatorio; frontend libre |
| Plataforma | Web responsive **mobile-first**. Sin app nativa ni PWA en el MVP |
| Equipo / plazo | 3-5 personas, dedicación parcial, 4-8 semanas |
| Alcance geográfico | **Multi-ciudad por diseño**, sin ciudad hardcodeada |
| Oferta inicial | Sin ETL. Seed manual del equipo + carga de oferentes reales |
| Mapas | OpenStreetMap, sin costo ni tarjeta |
| Recurrencia | Fuera del MVP. Solo eventos únicos (con el modelo preparado) |
| Roles | **Cuentas separadas** demandante / oferente desde el registro |
| Categorías | Catálogo **cerrado**, **varias por evento** |
| Radio de búsqueda | **Viewport**: se busca lo que entra en el rectángulo visible del mapa |
| Autenticación | Email + contraseña propio (sin login social) |
| Experiencia del equipo | React/TS y SQL sí; backend Python y Docker **no** |
| Features opcionales | Ninguna entra al MVP (sin favoritos, sin publicidad, sin analítica) |

---

## 2. Stack tecnológico propuesto

### Backend — **Django 5 + Django REST Framework**, Python 3.12

La restricción es backend Python y el equipo **no tiene experiencia en backend Python**. Con ese
dato, el criterio de selección no es la elegancia del framework sino cuánto trabajo te evita
escribir. Django trae resueltos, sin código propio, exactamente los cuatro bloques que el MVP
necesita y que en otro framework habría que construir: autenticación con hashing seguro de
contraseñas, migraciones de esquema versionadas, ORM sobre SQL (terreno que el equipo *sí*
domina) y un **panel de administración autogenerado**.

Ese panel merece un párrafo aparte porque resuelve un problema de producto, no solo técnico: es
la herramienta con la que el equipo va a cargar el seed manual de eventos y con la que se van a
moderar publicaciones. Sin él, el seed se carga por scripts o hay que construir un backoffice.
Son días de trabajo que Django te regala.

**Alternativas evaluadas y descartadas:**

- **FastAPI + SQLAlchemy + Alembic + Pydantic.** Es la opción más alineada con tus preferencias
  declaradas (pydantic, asyncio, tipado) y técnicamente la más limpia: validación por tipos,
  OpenAPI automático, async nativo. **Se descarta por plazo**: obliga a implementar a mano
  registro, hashing, emisión y refresco de tokens, y el backoffice de carga. Estimo 1,5-2
  semanas adicionales sobre un plazo de 4-8 — entre un 25% y un 50% del proyecto — a cargo de un
  equipo que además está aprendiendo Python web. El async, además, no aporta acá: la carga es
  I/O contra una sola base de datos con pocos usuarios concurrentes, no hay nada que paralelizar.
  **Es la opción correcta para la fase 2**, si el proyecto sigue vivo y el equipo ya tiene
  rodaje en Python.
- **Flask.** Minimalista; arrastra las mismas carencias que FastAPI (auth, migraciones,
  backoffice) sin ofrecer a cambio el tipado ni la documentación automática. Peor en ambos ejes.
- **Django con templates, sin DRF (monolito).** Sería aún más rápido de entregar, pero choca con
  dos definiciones tuyas: el equipo sabe React y no sabe Python, así que el trabajo de frontend
  rendiría mucho menos; y cierra la puerta a una app nativa futura, que es justamente el motivo
  por el que elegiste "TP ahora, producto después".
- **Next.js full-stack.** Descartado directamente por la restricción de backend en Python.

### Base de datos — **PostgreSQL 16, sin PostGIS**

Esto es contraintuitivo y conviene entender por qué. Al elegir búsqueda **por viewport**, la
consulta geoespacial se reduce a un rectángulo:

```sql
WHERE latitud  BETWEEN :sur  AND :norte
  AND longitud BETWEEN :oeste AND :este
```

Eso es un simple rango sobre dos columnas numéricas. Un índice B-tree compuesto lo resuelve en
tiempo logarítmico y no requiere ninguna extensión geoespacial. **PostGIS agrega una dependencia
de infraestructura no trivial —para un equipo sin experiencia en Docker— a cambio de capacidades
que el MVP no usa** (distancias geodésicas exactas, polígonos, índices GiST). Entra en la fase 2,
cuando aparezcan "ordenar por cercanía real" o "eventos dentro de este barrio".

Complejidad de la consulta principal: **O(log n + k)** con `k` = eventos en el viewport, contra
**O(n)** de un scan completo. Con el seed del TP (cientos de filas) la diferencia es invisible,
pero el índice correcto desde el día 1 no cuesta nada y es defendible en la evaluación.

- *Descartado — SQLite en producción*: se usa solo para la suite de tests (arranque instantáneo,
  aislamiento por test). En desarrollo y producción va PostgreSQL para que no haya divergencia
  de comportamiento entre entornos.
- *Descartado — MongoDB*: los datos son fuertemente relacionales (usuario → oferente → evento →
  categorías) y el equipo sabe SQL. No hay ningún argumento a favor.

### Frontend — **React 18 + TypeScript + Vite**

Es donde el equipo ya es productivo; con el plazo que hay, esto pesa más que cualquier otra
consideración. Vite por velocidad de arranque y cero configuración.

- **Mapa: Leaflet + react-leaflet**, con tiles raster de OpenStreetMap.
  *Descartado — MapLibre GL*: mejor rendimiento con muchos marcadores y tiles vectoriales, pero
  necesita un proveedor de estilos/tiles configurado aparte. Más setup del que justifica el MVP.
  *Descartado — Mapbox / Google Maps*: mejor calidad de datos, pero exigen cuenta con facturación.
- **Estado del servidor: TanStack Query.** Los filtros de búsqueda generan un caso clásico de
  cacheo por clave (viewport + fechas + horario + categorías); resolverlo a mano con `useEffect`
  produce race conditions cuando el usuario arrastra el mapa rápido. Esto es un bug real y
  frecuente, no una optimización prematura.
- Estilos: CSS Modules o Tailwind, indistinto. No es una decisión arquitectónica.

### Calidad y CI/CD (criterio de evaluación explícito de la cátedra)

- **Tests: pytest + pytest-django + factory_boy.** El foco de cobertura va sobre la lógica de
  búsqueda y filtrado, que es donde de verdad se rompen las cosas (bordes del viewport,
  antimeridiano, rangos de fecha invertidos, filtro de hora que cruza medianoche).
- **Lint/format: Ruff** (reemplaza flake8 + black + isort en una sola herramienta).
- **CI: GitHub Actions** en cada push y PR — ruff → pytest → build del frontend → vitest.
- **Flujo de trabajo:** `main` protegida, ramas por feature, merge solo vía PR con CI en verde y
  al menos una revisión. Al ser un ítem evaluado, conviene que el historial de PRs sea legible:
  es la evidencia del proceso.
- **Despliegue**: no es requisito de la cátedra. Si lo quieren igual, la vía sin tarjeta y sin
  Docker es Render o Fly.io para la API + Neon para PostgreSQL + Vercel/Netlify para el front.

---

## 3. Modelo de datos inicial

Convención: nombres en español para coincidir con el dominio y la documentación del TP.
Todos los timestamps se almacenan en **UTC** y se presentan en hora local.

### `Usuario`
Modelo base de autenticación (`AbstractBaseUser` de Django), con el email como identificador.

| Campo | Tipo | Notas |
|---|---|---|
| `id` | UUID | PK. UUID y no autoincremental: no filtra volumen de usuarios ni permite enumeración |
| `email` | str | **único**, login |
| `password_hash` | str | gestionado por Django (PBKDF2/Argon2). Nunca en texto plano |
| `nombre` | str | |
| `rol` | enum | `DEMANDANTE` \| `OFERENTE`. **Excluyente** (decisión: cuentas separadas) |
| `activo`, `creado_en` | bool, datetime | |

> El rol es excluyente por decisión de producto. Aun así vive en una sola tabla: si en el futuro
> se decide unificar cuentas, el cambio es relajar una validación, no una migración de datos.

### `PerfilOferente` (1:1 con `Usuario` donde `rol = OFERENTE`)

| Campo | Tipo | Notas |
|---|---|---|
| `usuario_id` | FK | PK y FK |
| `nombre_publico` | str | Lo que ve el demandante ("Bar Los Pinos") |
| `tipo` | enum | `PERSONA` \| `LOCAL` \| `MARCA` \| `ESTABLECIMIENTO` |
| `descripcion`, `sitio_web`, `telefono_contacto` | | opcionales |
| `verificado` | bool | **default `False`, sin flujo de verificación en el MVP.** El campo existe para que la insignia y el proceso de validación de identidad se puedan agregar en fase 2 sin migrar |

### `PerfilDemandante` (1:1 con `Usuario` donde `rol = DEMANDANTE`)
Prácticamente vacío en el MVP (`usuario_id`, `ciudad_referencia` opcional). Existe como punto de
anclaje para favoritos y ubicaciones guardadas de la fase 2.

### `Evento` — entidad central

| Campo | Tipo | Notas |
|---|---|---|
| `id` | UUID | PK |
| `oferente_id` | FK → `PerfilOferente` | |
| `titulo`, `descripcion` | str, text | |
| `inicio_utc`, `fin_utc` | datetime | `fin` opcional |
| `hora_inicio_local` | smallint (0-23) | **denormalizado a propósito**: permite indexar el filtro de rango horario. Sin esto, `EXTRACT(HOUR FROM ...)` fuerza un scan completo |
| `lugar_nombre`, `direccion` | str | |
| `latitud`, `longitud` | decimal(9,6) / (9,6) | 6 decimales ≈ 10 cm de precisión, de sobra |
| `precio_desde` | decimal, null | `null` = sin dato; `0` = gratis. **No son lo mismo** |
| `url_externa` | str, null | Link a entradas o a la publicación original |
| `estado` | enum | `BORRADOR` \| `PUBLICADO` \| `CANCELADO` \| `OCULTO` (`OCULTO` = bajado por moderación) |
| `origen` | enum | `CARGA_OFERENTE` \| `SEED_EQUIPO` \| `IMPORTADO`. Hoy nunca vale `IMPORTADO`; **el campo existe desde el día 1 para que la ingesta de fase 2 no requiera migración y para poder distinguir el dataset de demo del contenido real** |
| `serie_id` | UUID, null | Siempre `null` en el MVP. Gancho para la recurrencia (RRULE) de fase 2 |
| `destacado_hasta` | datetime, null | Siempre `null` en el MVP. Gancho para la publicidad de fase 2 |
| `creado_en`, `actualizado_en` | datetime | |

**Índices:**
- `(estado, inicio_utc, latitud, longitud)` — cubre la consulta principal de búsqueda
- `(oferente_id, inicio_utc)` — listado "mis eventos" del oferente

### `Categoria` — catálogo cerrado (fixture versionada en el repo)
`id`, `slug`, `nombre`, `icono`, `activa`.
Propuesta inicial: bar · recital · teatro · cine · deportivo · museo · gastronomía · feria ·
taller · aire libre · otro.

### `EventoCategoria` — tabla intermedia N:M
`evento_id`, `categoria_id`. PK compuesta. Habilita varias categorías por evento (decisión
tomada) y el filtro es un `IN` sobre esta tabla.

### Decisiones de modelado que conviene tener explícitas

1. **No existe entidad `Lugar` en el MVP.** La dirección y las coordenadas viven denormalizadas
   dentro de `Evento`. Ventaja: la consulta de búsqueda golpea una sola tabla, sin joins.
   Desventaja real: un bar que publica 20 fechas retipea la dirección 20 veces. Extraer `Lugar`
   es refactor limpio (crear tabla, backfill por dirección normalizada, agregar FK) y está
   listado en fase 2. **Si el modelo de uso resulta ser mayoritariamente locales fijos publicando
   agenda, esta decisión hay que revisarla temprano.**
2. **Multi-ciudad por diseño, sin entidad `Ciudad`.** No hay tabla de ciudades ni campo ciudad
   en `Evento`: la búsqueda es puramente geométrica sobre lat/long. Consecuencia buscada: sumar
   una ciudad nueva es cargar eventos, nunca tocar código ni migrar. Consecuencia a aceptar: no
   se puede filtrar "por ciudad" como concepto — se filtra por área del mapa, que es lo que la
   interfaz ofrece de todos modos.
3. **Zona horaria.** Argentina es UTC-3 sin horario de verano, así que hoy no duele. Guardar UTC
   igual es lo correcto y evita una migración dolorosa si algún día hay eventos fuera del país.

---

## 4. Alcance

### MVP — lo que entra

**Autenticación y cuentas**
- Registro con email + contraseña, eligiendo rol (demandante u oferente) en el registro
- Login / logout con JWT (`djangorestframework-simplejwt`); el access token se mantiene en
  memoria, nunca en `localStorage`
- Perfil básico editable

**Oferente**
- Alta, edición y baja de eventos únicos
- Ubicación: **el oferente marca el punto arrastrando un pin en el mapa** (el valor autoritativo
  son las coordenadas, la dirección escrita es descriptiva). Esto evita depender de geocoding y
  elimina de raíz el problema de direcciones argentinas mal interpretadas
- Selección de una o varias categorías del catálogo cerrado
- Listado "mis eventos" con estado

**Demandante — descubrimiento (el corazón del producto)**
- **Vista mapa**: se centra con la Geolocation API del navegador; marcadores de eventos; búsqueda
  por viewport, que se re-dispara (con debounce) al mover o hacer zoom
- **Vista lista**: mismos resultados, mismos filtros, ordenados por fecha de inicio
- **Filtros**: rango de fechas, rango horario, categorías (multi-selección, opcional)
- **Ubicación alternativa**: buscador de ciudad/lugar vía Nominatim, con debounce, caché local y
  `User-Agent` identificatorio, para explorar oferta de un destino sin estar ahí
- **Fallback si se rechaza el permiso de ubicación**: se abre con una ubicación por defecto y el
  buscador de ciudad visible. **El producto tiene que ser plenamente usable sin permiso de
  geolocalización** — es un porcentaje real de usuarios, no un caso borde
- **Estado vacío honesto**: si no hay resultados, decir explícitamente cuál filtro los está
  eliminando y ofrecer la acción correctiva ("ampliá el rango de fechas", "alejá el mapa"),
  nunca una pantalla en blanco
- Ficha de detalle del evento con datos del oferente

**Contenido y operación**
- Seed manual del equipo vía panel de administración de Django, marcado con `origen = SEED_EQUIPO`
- Moderación reactiva: un admin puede pasar cualquier evento a `OCULTO` desde el panel

**Ingeniería (evaluable)**
- Suite de tests con foco en la lógica de búsqueda
- Pipeline de GitHub Actions, `main` protegida, flujo de PRs
- README con arquitectura, decisiones y guía de puesta en marcha

### Fuera del MVP — fase 2, en orden de prioridad

1. **Ingesta de fuentes externas (ETL).** Es el ítem #1 y no es negociable si el producto se
   lanza de verdad: el seed manual es un dataset de demo, no una estrategia de contenido. Implica
   conectores por fuente, normalización, geocoding, deduplicación y scheduler. Ojo con los
   límites: Nominatim permite 1 req/s y su política **prohíbe explícitamente el geocoding masivo**
   — geocodificar un import grande por ahí termina en bloqueo de IP. Esto obliga a un geocoder
   pago o a instancia propia, y es un costo que hay que presupuestar antes de prometer la feature.
2. **Favoritos y ubicaciones guardadas** (habilitan retención y, después, notificaciones).
3. **Eventos recurrentes** (`Serie` + RRULE + materialización de ocurrencias + excepciones).
4. **Entidad `Lugar`** con reutilización de direcciones por parte del oferente.
5. **Verificación de oferentes** (anti-suplantación) y reportes de usuarios.
6. **Notificaciones** ("hay algo nuevo cerca de una ubicación que guardaste").
7. **Publicidad / eventos destacados** + integración con Mercado Pago.
8. **Dashboard de analítica para oferentes** (vistas, clicks, alcance).
9. **Reseñas y calificaciones.**
10. **App nativa / PWA**, si el uso mobile lo justifica.

### Por qué la publicidad queda fuera, explícitamente

Es la decisión de recorte que más conviene tener justificada de cara a la defensa del TP.
Cobrar por posicionamiento requiere pasarela de pago, facturación, un modelo de pricing y un
algoritmo de ranking. Pero sobre todo requiere **tráfico**: "aparecer primero" ante cero usuarios
no vale nada, así que no hay nada que vender todavía. El campo `destacado_hasta` ya está en el
modelo, de modo que cuando llegue el momento la feature es ordenar por él y enchufar el cobro —
no rediseñar el esquema.

---

## 5. Riesgos abiertos

| Riesgo | Impacto | Mitigación |
|---|---|---|
| **Nadie en el equipo sabe backend Python** | Alto — es el riesgo de cronograma dominante | Django justamente por esto. Reservar la semana 1 completa a tutorial + esqueleto. Emparejar a quien tenga más afinidad con Python en el backend |
| **Mapa vacío** (sin ETL) | Alto para el producto, medio para el TP | El seed manual tiene que cubrir bien 1-2 zonas: 30 eventos concentrados se ven vivos, 30 dispersos por el país se ven muertos. Priorizar densidad sobre cobertura |
| **Política de uso de tiles de OSM** | Medio | El volumen de un TP está dentro de lo aceptable, pero la política prohíbe uso pesado. Si el producto crece, hay que pasar a un proveedor de tiles |
| **Spam / eventos falsos** | Bajo hoy, alto al abrir | Hoy lo contiene el volumen bajo + moderación manual por panel. Antes de cualquier apertura real hacen falta reportes y verificación |
| **Datos personales (Ley 25.326)** | Medio | No guardar histórico de ubicaciones en el MVP: la ubicación se usa en la sesión y no se persiste. Sumar política de privacidad antes de tener usuarios reales |

---

## 6. Plan de ejecución sugerido (6 semanas, 4 personas)

| Semana | Backend | Frontend | Transversal |
|---|---|---|---|
| 1 | Setup Django + Postgres, modelos, migraciones | Setup Vite + React + ruteo | **CI andando desde el día 1**, `main` protegida |
| 2 | Auth (registro/login/JWT) | Pantallas de auth, cliente de API | Primeros tests |
| 3 | CRUD de eventos + endpoint de búsqueda | Formulario de carga con pin en mapa | Tests de búsqueda |
| 4 | Filtros, índices, paginación | Vista mapa con viewport y marcadores | Seed manual cargado |
| 5 | Ajustes, panel de admin | Vista lista, filtros, buscador de ciudad | Tests de integración |
| 6 | — | Estados vacíos, responsive, pulido | README, documentación, ensayo de demo |

Regla de oro: **el CI tiene que estar verde desde la semana 1**. Es un ítem evaluado y montarlo
al final siempre sale mal.

---

## 7. Decisiones pendientes que necesito de vos

Ninguna bloquea el arranque (semanas 1-2 se pueden ejecutar ya), pero las 4 primeras hay que
cerrarlas antes de que el trabajo las alcance.

1. **Zonas del seed manual.** ¿Cuáles 1-2 zonas concretas? Definen dónde el mapa se ve vivo el
   día de la demo. *(Necesario para la semana 4)*
2. **Catálogo de categorías definitivo.** ¿Confirmás las 11 propuestas o querés agregar/quitar?
   Es una fixture versionada: cambiarla después implica migración de datos. *(Semana 1)*
3. **¿El evento necesita imagen?** No lo mencionaste nunca y cambia el alcance de forma no
   trivial: subida de archivos, almacenamiento, redimensionado, y un mapa sin fotos se ve
   notablemente más pobre. **Mi recomendación: una sola imagen de portada por evento, opcional,
   guardada en disco local.** *(Semana 3)*
4. **¿Qué pasa con un evento cuando termina?** ¿Desaparece de la búsqueda al instante, sigue
   visible hasta fin del día, o queda accesible por URL directa? Afecta el filtro por defecto.
   *(Semana 3)*
5. **Idioma de la interfaz y del código.** Propuse dominio en español; hay que confirmar si el
   código va en español también o en inglés con dominio en español. *(Semana 1, conviene cerrarlo
   ya para no mezclar)*
6. **¿Hay que desplegar?** No lo marcaste como requisito de la cátedra. Si igual lo querés, hay
   que reservar ~3 días de la semana 6.
7. **Nombre del producto.** No es urgente, pero aparece en el README, la interfaz y la defensa.
