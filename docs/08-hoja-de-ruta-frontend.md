# Hoja de ruta del frontend

## Plataforma de descubrimiento de eventos por geolocalización

**Fecha:** 11/11/2026 (actualizado el 13/11/2026) · **Stack:** React 19 + Vite + JavaScript, React Router 7, TanStack Query 5

Plan para implementar el frontend de los requisitos **Must** (`02-requisitos-funcionales.md`). El
backend de todos ya está hecho (`06-estado-de-implementacion.md`), así que el trabajo que queda es
casi todo de frontend. Este documento se actualiza a medida que se avanza: al terminar algo,
cambiar su **Estado** en la tabla.

---

## Punto de partida

Lo que ya está hecho y no hay que volver a resolver:

| Pieza | Dónde | Qué resuelve |
|---|---|---|
| Proxy a la API | `frontend/vite.config.js` | `/api/...` → backend en `localhost:8000`, incluida la cookie del refresh token |
| Cliente HTTP | `src/services/client.js` | Token, renovación de sesión ante un 401, errores del backend como `ApiError` |
| Servicios | `src/services/` | Todos los endpoints de `/auth`, `/eventos`, `/categorias`, `/config`, `/geocodificacion` y la solicitud de `/organizadores`. Las consultas aceptan `{ signal }` para que TanStack Query cancele las que quedan viejas |
| Sesión | `src/features/auth/context/AuthContext.jsx` | `useAuth()`: usuario, `login`, `logout`, `refrescarUsuario`, restauración al recargar. `user` tiene siempre la forma de `GET /auth/me`: `{ id, email, nombre, apellido, organizador: { id_organizador, nombre_publico, estado } \| null, es_admin }` |
| Rutas privadas | `src/routes/PrivateRoute.jsx`, `OrganizadorRoute.jsx` | Redirige a `/ingresar` sin sesión y vuelve a la página pedida después del login. `OrganizadorRoute` deja pasar solo a organizadores `APROBADO` |
| Caché de datos del servidor | `src/queryClient.js`, `src/main.jsx` | `QueryClientProvider` envuelve la app. Un dato se considera actual durante 30 s; solo se reintentan las fallas de red y los 5xx (un 4xx daría lo mismo y el 401 lo resuelve `client.js`); las mutaciones no se reintentan. `AuthContext` vacía la caché al cerrar sesión o cuando la sesión vence |
| Paleta de colores | `src/index.css` | Variables en `:root` (escala slate: base, botones, mensajes) redefinidas en `prefers-color-scheme: dark`. Los componentes no usan colores fijos, solo estas variables |
| Navegación | `src/components/layout/` | `Layout` con `BarraNavegacion` y `<Outlet />` para las rutas privadas (ver etapa 1, paso 3) |
| Componentes de interfaz | `src/components/ui/` | `Button`, `Input`, `PasswordInput`, `Textarea`, `Select`, `FormField`, `FormError`, `SubmitButton`, `Spinner`, `Badge`, `EmptyState`, `ConfirmDialog`, `Icono` y `Avatar`. Cada uno documenta su uso en un comentario al principio del archivo. En desarrollo, `/dev/componentes` los muestra todos (ver etapa 1, paso 4) |
| Íconos | `index.html`, `src/components/ui/Icono.jsx` | Material Symbols Outlined con el eje de relleno variable: `<Icono nombre="explore" relleno />`. Los nombres están en [fonts.google.com/icons](https://fonts.google.com/icons) |
| Envío de formularios | `src/hooks/useFormSubmit.js` | Estado de envío y errores del backend mostrados en cada campo |
| Login y registro | `src/features/auth/components/` | Formularios completos |
| Perfil | `src/pages/Perfil.jsx` | Datos de la cuenta, roles (organizador con su estado, administrador) y "Cerrar sesión" |
| Página 404 | `src/pages/NoEncontrado.jsx` | Ruta `*`, con o sin sesión. `/` redirige a `/explorar` |

Decisiones de `planning.md` que aplican al frontend:
- **Mapa: Leaflet + react-leaflet** con tiles de OpenStreetMap.
- **TanStack Query** para los datos del servidor, sobre todo para la búsqueda: los filtros y el
  viewport cambian seguido y, hecho a mano con `useEffect`, aparecen respuestas viejas que pisan a
  las nuevas cuando se arrastra el mapa rápido.

---

## Pendientes del backend que bloqueaban al frontend

Ya resueltos; la etapa 3 y la 4 quedan desbloqueadas.

| # | Problema | Qué afecta | Solución | Estado |
|---|---|---|---|---|
| B-1 | El frontend no tiene forma de saber si el usuario es organizador (y en qué estado) ni si es administrador | Mostrar u ocultar "Crear evento", "Mis eventos", "Solicitar ser organizador" y las acciones de admin (RF-01.6, RF-01.7, RF-05.1) | `GET /auth/me` (`app/perfil/`) devuelve `UsuarioPublic` + `organizador: { id_organizador, nombre_publico, estado } \| null` + `es_admin` | Hecho |
| B-2 | Después del login el usuario es `{ id, email, nombre, apellido }`, pero al recargar es `{ usuario_id, email }`: `verify-session` no devuelve el resto | Cualquier pantalla que muestre el nombre o use `user.id` | `iniciarSesion()` y `restaurarSesion()` (`services/auth.js`) piden `GET /auth/me`. `useAuth()` suma `refrescarUsuario()` para actualizar los roles sin otro login (p. ej. después de solicitar ser organizador) | Hecho |
| B-3 | Los errores de validación de Pydantic llegan en inglés ("value is not a valid email address") | Formularios de registro y de eventos | Se traducen en el backend (`app/core/validation_errors.py`) con el mismo formato `{ detail: [{ loc, msg, type }] }`, así `useFormSubmit` no cambia | Hecho |

---

## Requisitos Must

**Estados:** `Hecho` · `Parcial` (hay una parte hecha) · `Pendiente` · `Bloqueado` (depende de un
pendiente del backend de la tabla anterior). La columna **Etapa** remite a la secuencia de la
sección siguiente.

### RF-01 · Cuentas y autenticación

| # | Requisito | Implementación en el frontend | Etapa | Estado |
|---|---|---|---|---|
| RF-01.1 | Registro con nombre, apellido, email y contraseña | Página `/registro` con `FormField` + `Input` y `useFormSubmit`, llamando a `registrar()` (ya existe en `auth.js`). Validar en el navegador contraseña de 8 a 128 caracteres. El backend no inicia sesión al registrar: después del alta, llamar a `login()` con los mismos datos para entrar directo. Un `409` (email ya registrado) aparece solo en `FormError`. | 1 | Hecho |
| RF-01.2 | Todo usuario registrado puede descubrir eventos | Todas las rutas de descubrimiento (`/explorar`, `/eventos/:id`) van dentro de `PrivateRoute`, sin exigir ningún rol. | 2 | Hecho |
| RF-01.3 | Iniciar y cerrar sesión | Login hecho. "Cerrar sesión" (`logout()` de `useAuth`) está en el menú de la cuenta, al pie de la barra lateral (`MenuCuenta`), y en `/perfil`, que es el único lugar en el celular. `/` redirige a `/explorar` (sin sesión, `PrivateRoute` lleva a `/ingresar`). | 1 | Hecho |
| RF-01.6 | Solicitar ser organizador (queda `PENDIENTE`) | Página `/organizador/solicitud` con `nombre_publico` y `descripcion` (`Textarea`). Nuevo `services/organizadores.js` con `solicitarOrganizador()` → `POST /organizadores/solicitud`. Mensajes para `409` (ya tiene una solicitud pendiente o aprobada) y `403` (perfil suspendido). Si la solicitud está pendiente, mostrar ese estado en lugar del formulario (`user.organizador.estado === 'PENDIENTE'`); después de enviarla, llamar a `refrescarUsuario()`. Llevan a esta ruta el ítem "Ser organizador" de la barra (sin perfil, `RECHAZADO` o `PENDIENTE`; no se muestra a `APROBADO` ni a `SUSPENDIDO`) y los enlaces "Solicitar"/"Ver" de `/perfil`. | 3 | Hecho |
| RF-01.7 | Solo un organizador `APROBADO` crea y edita eventos | `OrganizadorRoute`: igual que `PrivateRoute`, pero además exige `user.organizador.estado === 'APROBADO'`. La barra de navegación ya muestra "Crear evento" y "Mis eventos" solo a ellos (`BarraNavegacion`); `OrganizadorRoute` protege `/mis-eventos`, `/eventos/nuevo` (y después `/eventos/:id/editar`): al resto lo manda a `/organizador/solicitud`, que explica su caso, con un aviso de que hace falta un perfil aprobado. El backend igual valida (`403`), esto es para no ofrecer acciones que van a fallar. | 3 | Hecho |

### RF-02 · Gestión de eventos (organizador)

| # | Requisito | Implementación en el frontend | Etapa | Estado |
|---|---|---|---|---|
| RF-02.1 | Alta de evento: título, descripción, inicio, fin y precio opcionales | Página `/eventos/nuevo` con `FormularioEvento` → `crearEvento()`. Fechas con `<input type="datetime-local">` interpretadas en la zona de la plataforma (`deValorFechaHora` en `formato.js`) y mandadas en ISO. Precio `type="number"` con `min="0"` y `step="0.01"`; vacío va como `null` (no se muestra precio). Se valida en el navegador que el inicio sea futuro y el fin posterior al inicio. | 3 | Hecho |
| RF-02.2 | Ubicar el evento marcando un punto en el mapa | `SelectorUbicacion`: usa el mismo componente `Mapa` de la etapa 2, con un marcador arrastrable que también se mueve con un clic. Reutiliza `BuscadorLugar` para centrar el mapa en una dirección. Envía `lugar: { latitud, longitud, nombre?, direccion? }`: las coordenadas mandan, nombre y dirección son descriptivos. | 3 | Hecho |
| RF-02.3 | Asociar una o varias categorías del catálogo | `SelectorCategorias` (el mismo de los filtros, RF-03.6) con al menos una seleccionada. Muestra `nombre` y envía `slug`. | 3 | Hecho |
| RF-02.4 | Editar y cancelar un evento propio | `/eventos/:id/editar` reutiliza `FormularioEvento`, cargado con `obtenerEvento()`, y manda solo los campos modificados con `editarEvento()` (PATCH). Botón "Cancelar evento" con `ConfirmDialog` → `cancelarEvento()`. Ambas acciones solo se habilitan si el estado es `BORRADOR` o `PUBLICADO` (si no, el backend responde `409`); cancelar, además, si el evento no terminó. | 3 | Hecho |
| RF-02.5 | Listado "mis eventos" con su estado | Página `/mis-eventos` con `listarMisEventos()`. Cada fila tiene un `BadgeEstado` (`BORRADOR`, `PUBLICADO`, `CANCELADO`, `OCULTO`) y las acciones editar/cancelar de RF-02.4. Estado vacío con un enlace a "Crear evento". | 3 | Hecho |

### RF-03 · Descubrimiento y búsqueda

| # | Requisito | Implementación en el frontend | Etapa | Estado |
|---|---|---|---|---|
| RF-03.1 | Vista de mapa centrada en la ubicación del usuario | Página `/explorar` con `MapaEventos` (react-leaflet + tiles OSM con su atribución). Hook `useUbicacionInicial`: pide `navigator.geolocation` con un timeout corto; si falla, usa `GET /config/ubicacion-default` (`lat`, `lng`, `zoom`). Un marcador por evento en `lugar.latitud/longitud`, con un popup que lleva al detalle. La posición del mapa queda en la URL (`?lat=&lng=&zoom=`): al volver de la ficha no se vuelve a pedir la ubicación. | 2 | Hecho |
| RF-03.2 | Vista de lista con los mismos resultados que el mapa | `ListaEventos` con `TarjetaEvento`, alimentada por el **mismo** hook `useBusquedaEventos` que el mapa, así nunca pueden mostrar cosas distintas. Mapa y lista lado a lado en escritorio, con selector en mobile. Paginación con `limit`/`offset` ("Cargar más"). | 2 | Hecho |
| RF-03.3 | Mover y hacer zoom re-ejecuta la búsqueda por viewport | En los eventos `moveend`/`zoomend` de Leaflet, leer `map.getBounds()` → `lat_min`, `lat_max`, `lng_min`, `lng_max`, con un debounce de unos 400 ms. `useBusquedaEventos` usa TanStack Query con el viewport y los filtros como clave de caché. Ojo: Leaflet puede devolver longitudes fuera de -180..180 si el mapa se repite horizontalmente, y el backend las rechaza (`422`); limitarlas o usar `worldCopyJump`/`maxBounds`. | 2 | Hecho |
| RF-03.4 | Filtrar por rango de fechas | `PanelFiltros` con dos `<input type="date">` → `desde`, `hasta`. Los filtros se guardan en la URL (`useSearchParams`), así sobreviven a una recarga y se pueden compartir. | 2 | Hecho |
| RF-03.5 | Filtrar por rango horario | Dos `<input type="time">` en `PanelFiltros` → `hora_desde`, `hora_hasta` (`HH:MM`). | 2 | Hecho |
| RF-03.6 | Filtrar por una o varias categorías | `SelectorCategorias` en modo filtro (sin selección = todas) → `categorias` como lista; `client.js` ya la manda repitiendo el parámetro. | 2 | Hecho |
| RF-03.7 | Buscar una ubicación distinta a la actual | `BuscadorLugar`: input con debounce que busca desde 3 caracteres (mínimo del backend) → nuevo `services/geocodificacion.js` → `GET /geocodificacion/buscar?q=`. Al elegir una sugerencia, `map.fitBounds()` con su bounding box, que tiene los mismos nombres que el viewport. Mensajes para `[]` ("sin coincidencias") y `503` ("el buscador no está disponible"). | 2 | Hecho |
| RF-03.8 | Usable sin permiso de geolocalización | Si se rechaza el permiso o vence el timeout, `useUbicacionInicial` usa la ubicación por defecto y la página muestra `BuscadorLugar` destacado, con un aviso que no bloquea ("No pudimos obtener tu ubicación, mostramos *{nombre}*"). Probarlo rechazando el permiso en el navegador. | 2 | Hecho |
| RF-03.10 | Ficha de detalle con los datos del organizador | Página `/eventos/:id` con `obtenerEvento()`: datos del evento, categorías, un mapa chico con el lugar y el bloque "Publicado por" con `organizador.nombre_publico` y `descripcion` (para los eventos de seed, el backend ya manda "Equipo de la plataforma"). Un `404` muestra "Evento no encontrado". | 2 | Hecho |

### RF-04 · Categorías

| # | Requisito | Implementación en el frontend | Etapa | Estado |
|---|---|---|---|---|
| RF-04.1 | Catálogo cerrado de categorías | Nuevo `services/categorias.js` → `GET /categorias` (público). Se cachea con TanStack Query con un `staleTime` largo, porque el catálogo casi no cambia. Lo usan `SelectorCategorias` (filtros y formulario) y las tarjetas. | 2 | Hecho |
| RF-04.2 | Varias categorías por evento | Cubierto por `SelectorCategorias` en `FormularioEvento` (RF-02.3). `TarjetaEvento` y el detalle muestran todas las categorías del evento como chips. | 3 | Hecho |

### RF-05 · Moderación y contenido

| # | Requisito | Implementación en el frontend | Etapa | Estado |
|---|---|---|---|---|
| RF-05.1 | Un administrador oculta cualquier evento publicado | En el detalle (RF-03.10), botón "Ocultar evento" visible solo para administradores, con `ConfirmDialog` → `ocultarEvento()` (ya existe en `eventos.js`). Después vuelve a `/explorar`, porque el evento deja de verse. | 4 | Pendiente |
| RF-05.2 | Eventos del equipo (seed) diferenciados | La carga es por script (`scripts/seed.py`), así que en el frontend no hay formulario. Solo hay que diferenciarlos: `BadgeEquipo` ("Equipo de la plataforma", variante `info`) cuando `origen === 'SEED_EQUIPO'`, en `TarjetaEvento` antes de las categorías y en el detalle arriba del título. En "Publicado por" el detalle muestra el logo de la app en lugar de iniciales. | 2 | Hecho |

### Recomendado aunque no es Must

| # | Requisito | Implementación en el frontend | Etapa | Estado |
|---|---|---|---|---|
| RF-05.5 (S) | Un administrador aprueba, rechaza y suspende organizadores | Página `/admin/organizadores` con pestañas por estado → `GET /admin/organizadores?estado=` y acciones aprobar/rechazar/suspender. El backend ya está. **Sin esta pantalla no se puede probar de punta a punta el flujo de organizador** (RF-01.6 → RF-01.7 → RF-02.x) sin llamar a la API a mano. El ítem "Administración" de la barra ya aparece solo para administradores; la ruta hoy muestra `EnConstruccion`. | 4 | Pendiente |

---

## Secuencia de implementación

El orden sigue dos criterios:
1. **Primero el descubrimiento**: es "el corazón del producto" según `planning.md` y contiene el
   único Must que faltaba en todo el proyecto (RF-03.1, hecho en la etapa 2).
2. **Construir antes lo que se reutiliza**: el `Mapa` y el `SelectorCategorias` de la etapa 2 los
   vuelve a usar el formulario de eventos de la etapa 3.

### Etapa 0 · Base (hecha)
Vite + proxy, `client.js` y servicios, `AuthContext`, `PrivateRoute`, componentes de formulario y Login.

### Etapa 1 · Estructura de la app y registro (hecha)
Cierra **RF-01.1** y **RF-01.3**.
1. ~~Pasar los colores de `Button.css` e `Input.css` a las variables de `index.css`, para que
   funcionen en modo claro y oscuro.~~ **Hecho.** También se pasaron `PasswordInput`, `FormField`,
   `FormError` y el aviso de `Auth.css`; no queda ningún color fijo fuera de `index.css`.
2. ~~Instalar TanStack Query y envolver la app en `QueryClientProvider`.~~ **Hecho** (ver
   `queryClient.js` en el punto de partida).
3. ~~`Layout` con `Header` y `<Outlet />`.~~ **Hecho, con una barra de navegación lateral en lugar
   del header**, al estilo de Instagram y X web. Mobile-first, en tres tamaños:
   - menos de 768px: barra de pestañas fija abajo, solo íconos; "Crear evento" es un botón
     relleno al medio;
   - desde 768px: columna fija a la izquierda, solo íconos (el nombre aparece al pasar el mouse);
   - desde 1264px: barra lateral con textos, el botón "Crear evento" (como "Postear" en X) y la
     cuenta al pie, con un menú para "Cerrar sesión".

   Los ítems dependen de los roles de `GET /auth/me`: "Explorar" y "Perfil" para todos, "Mis
   eventos" y "Crear evento" para organizadores aprobados, "Ser organizador" para el resto y
   "Administración" para administradores. El ítem activo muestra el ícono relleno y el texto en
   negrita; "Perfil" muestra las iniciales del usuario. Se agregó `/perfil` (no estaba planificada)
   y las rutas que todavía no tienen página muestran `EnConstruccion` (ver el mapa de rutas). El
   nombre del producto es provisorio ("Eventos", `NOMBRE_APP` en `BarraNavegacion.jsx`) hasta
   que se defina (`planning.md`, pendiente 7).
4. ~~Componentes genéricos que van a hacer falta en todas las etapas.~~ **Hecho:**
   - `Spinner`: reemplaza el "Cargando..." de `PrivateRoute` (aparece a los 300 ms, para que las
     cargas rápidas no parpadeen) y se muestra en `SubmitButton` mientras se envía.
   - `Textarea` y `Select`: misma base visual que `Input` y conectados a `FormField`. `Textarea`
     tiene un contador opcional (`contador` + `maxLength`); `Select` es el `<select>` nativo con
     `placeholder` (una primera opción vacía que no se puede elegir).
   - `Badge`: variantes `neutral`, `exito`, `advertencia`, `error` e `info`. `BadgeEstado` (etapa
     3) se arma encima; ya se usa en `/perfil` para el estado del organizador.
   - `EmptyState`: ícono, título, descripción y una acción opcional. `EnConstruccion` lo usa.
   - `ConfirmDialog`: `<dialog>` nativo modal. `onConfirmar` puede ser async: mientras corre se
     deshabilitan los botones y, si falla, el error del backend se muestra en el diálogo, que queda
     abierto. Se cierra con "Volver", Escape o un clic afuera. El botón para cerrar dice "Volver" y
     no "Cancelar" para no confundirlo con "Cancelar evento".

   Se sumaron los colores `--warning-*`, `--info-*` y `--overlay` a la paleta. **`/dev/componentes`**
   muestra todos los componentes en un catálogo para revisar el diseño en claro y oscuro (incluye
   un `ConfirmDialog` que simula un `409`). Solo existe en desarrollo (`import.meta.env.DEV`): no
   entra en el build de producción ni aparece en la barra.
5. ~~Página de registro.~~ **Hecho.**
6. ~~Redirigir `/` a `/explorar` y agregar una página 404.~~ **Hecho.** `/` redirige a `/explorar`;
   sin sesión, `PrivateRoute` lleva a `/ingresar` y después del login se vuelve a `/explorar`. La
   404 (`NoEncontrado`, ruta `*`) queda fuera de `PrivateRoute` para no mandar a iniciar sesión y
   recién después avisar que la página no existe: con sesión se muestra dentro de `Layout` (que
   ahora también acepta `children`) con "Ir a Explorar"; sin sesión, sola y centrada con
   "Iniciar sesión". Los enlaces con forma de botón usan las clases de `Button` sobre un `Link`.
7. ~~Coordinar con el backend los pendientes B-1 y B-2.~~ Resueltos.

### Etapa 2 · Descubrimiento (CU-01 y CU-02) (hecha)
Cierra **RF-01.2**, **RF-03.1** a **RF-03.8**, **RF-03.10**, **RF-04.1** y **RF-05.2**.
1. ~~Servicios nuevos: `categorias.js`, `configuracion.js`, `geocodificacion.js`.~~ **Hecho:**
   `listarCategorias()` y `obtenerUbicacionDefault()` (públicas, sin token) y `buscarLugar(texto,
   { limit })`, que recorta los espacios; `MIN_CARACTERES_BUSQUEDA` (3) está exportado para que el
   buscador no llame antes de tiempo. `client.js` acepta un `signal` (`AbortSignal`) y lo pasa a
   `fetch`; `buscarEventos()`, `obtenerEvento()` y los servicios nuevos lo reciben en un último
   parámetro `{ signal }`, que es el que TanStack Query le da a cada consulta.
2. ~~`useBusquedaEventos(viewport, filtros)` con TanStack Query.~~ **Hecho**
   (`features/eventos/hooks/`). Devuelve `{ eventos, total, cargando, actualizando, error, hayMas,
   cargarMas, cargandoMas, reintentar }`:
   - `useInfiniteQuery` con páginas de 50 (`TAMANO_PAGINA`); `cargarMas()` pide la siguiente con
     `offset` y `eventos` las junta sin repetir. El mapa muestra lo mismo que la lista: lo cargado.
   - `normalizarViewport()` deja el viewport como lo acepta el backend: traslada las longitudes que
     Leaflet da fuera de -180..180, recorta lo que cruza el antimeridiano y redondea a 4 decimales
     hacia afuera (unos 11 m), así un movimiento mínimo no dispara otra búsqueda.
   - `normalizarFiltros()` descarta los vacíos y ordena las categorías: `['teatro', 'bar']` y
     `['bar', 'teatro']` comparten la caché.
   - Con `keepPreviousData`, al mover el mapa o cambiar un filtro se siguen viendo los resultados
     anteriores (`actualizando: true`) hasta que llegan los nuevos, y cada búsqueda cancela la
     anterior. El hook no hace debounce: lo hace el mapa (paso 5).
   - `habilitada: false` evita buscar antes de tener el primer viewport.
   - `clavesEventos.js`: todas las claves empiezan con `'eventos'`, para invalidarlas juntas después
     de crear, editar o cancelar un evento (etapa 3).
3. ~~**Primero la lista, sin mapa**: `TarjetaEvento` + `ListaEventos` + `PanelFiltros` (fechas,
   horario, `SelectorCategorias`) con los filtros en la URL.~~ **Hecho:** `/explorar` muestra la
   lista con `useBusquedaEventos(null, filtros)` (sin viewport hasta el paso 7).
   - `TarjetaEvento`: bloque de fecha, horario ("Mañana · 22:30 – 01:00", "hasta Dom 6 dic" si dura
     más de un día), lugar, categorías y precio ("Gratis" si es 0; sin precio no se muestra nada).
     Enlaza a `/eventos/:id`, que por ahora muestra `EnConstruccion`.
   - `ListaEventos`: esqueleto de carga, resultados anteriores atenuados mientras se actualiza,
     "Cargar más (n)", estados vacíos (con y sin filtros) y de error con "Reintentar".
   - `PanelFiltros`: categorías siempre a la vista (en el celular, una fila que se desliza) y fecha y
     horario en una sección desplegable; el botón resume lo elegido ("14 nov – 30 nov · 22:00 a
     02:00"). Los cambios se aplican enseguida. Si "desde" pasa a ser posterior a "hasta", se borra
     "hasta"; si el horario cruza la medianoche, se avisa.
   - `SelectorCategorias`: chips con `aria-pressed`, reutilizable en el formulario de eventos.
     `useCategorias()` pide el catálogo una vez por sesión (`staleTime: Infinity`).
   - `useFiltrosBusqueda()`: los filtros viven en la URL (`replace`, sin ensuciar el historial) y
     los valores mal formados se ignoran, así una URL vieja o escrita a mano no termina en un 422.
   - `formato.js`: las fechas se muestran en `America/Argentina/Buenos_Aires`, la misma zona con la
     que el backend aplica los filtros de fecha y horario. Una fecha que llega sin zona horaria
     (pasa con SQLite) se toma como UTC.
4. ~~Ficha de detalle `/eventos/:id`.~~ **Hecho** (`pages/DetalleEvento.jsx`, `useEvento`):
   - Título, categorías, cuándo (en dos renglones; si dura más de un día, "Hasta el domingo 6 de
     diciembre, 23:00"), lugar con un enlace "Abrir en OpenStreetMap", precio, descripción con sus
     saltos de línea y "Publicado por". Los eventos del seed muestran el logo de la app en lugar de
     iniciales.
   - Un evento cancelado muestra un aviso; los borradores (solo los ve su organizador) y los ya
     terminados, un badge.
   - Un `404` o un id que no es UUID (ni se pide) muestran "No encontramos este evento".
   - "Volver" regresa a la lista con sus filtros; si se entró directo por un enlace, dice
     "Explorar" y lleva ahí.
   - El mapa chico con el lugar se sumó en el paso 5 (`MapaUbicacion`).
5. ~~Instalar `leaflet` y `react-leaflet`. Crear un componente `Mapa` base (tiles, atribución,
   tamaño) y `MapaEventos` encima, con marcadores, popups y la búsqueda por viewport con debounce.
   Sumar con `Mapa` el mapa chico de la ficha de detalle (RF-03.10).~~ **Hecho** (`leaflet` 1.9.4,
   `react-leaflet` 5.0.0):
   - `components/mapa/Mapa`: tiles de OSM con su atribución (obligatoria), `minZoom` 3,
     `worldCopyJump` y `invalidateSize` cuando cambia el tamaño del contenedor. Controles y popups
     con la paleta de la app; en modo oscuro los tiles se invierten con un filtro CSS.
   - `marcador.js`: pin dibujado con CSS (`DivIcon`), porque las imágenes de Leaflet no se
     encuentran con Vite y no cambian con el tema. Con varios eventos en el mismo lugar muestra la
     cantidad.
   - `MapaEventos`: no busca por su cuenta. Avisa el viewport al montarse y cuando el usuario
     termina de mover o hacer zoom (`onCambioViewport`, debounce de 400 ms) y dibuja los
     `eventos` que le pasa la página. Agrupa los eventos con las mismas coordenadas en un marcador
     cuyo popup los lista; cada título lleva a la ficha. Muestra "Buscando..." con `actualizando`
     y expone la instancia de Leaflet por `ref` (para `fitBounds` en el paso 6). Los marcadores se
     enfocan con Tab y Enter abre su popup.
   - `MapaUbicacion`: el mapa chico de la ficha. No hace zoom con la rueda ni se arrastra con un
     dedo en pantallas táctiles, para no atrapar el scroll de la página.
   - Leaflet suma unos 50 kB comprimidos al bundle; si pesa, se puede cargar el mapa con `lazy`.
6. ~~`useUbicacionInicial` (geolocalización o ubicación por defecto) y `BuscadorLugar`.~~ **Hecho**
   (`features/ubicacion/`):
   - `useUbicacionInicial()` → `{ cargando, ubicacion: { lat, lng, zoom, nombre }, origen, motivo }`.
     Pide la ubicación del navegador y, en paralelo, la por defecto del backend. `origen` es
     `'usuario'` (zoom 14) o `'defecto'`, con `motivo`: `'denegado'`, `'sin-respuesta'`,
     `'no-disponible'` o `'no-soportado'`. Tiene un tope propio de 8 s, porque mientras el cartel de
     permiso está abierto el `timeout` de la geolocalización no corre; si el usuario acepta
     después, `ubicacion` cambia a la suya y la página tiene que recentrar el mapa. Si el backend
     tampoco responde, usa un respaldo fijo (Buenos Aires, el mismo valor por defecto del backend).
   - `BuscadorLugar` (`onSeleccionar(lugar)`, `destacado`): combobox con el patrón de ARIA (flechas,
     Enter, Escape cierra y después borra). Busca desde 3 letras y 500 ms después de la última
     tecla, cancela las búsquedas viejas y no vuelve a buscar al poner en el input el lugar
     elegido. Mensajes: "Buscando...", "No encontramos lugares para…" y, ante un `503`, "El
     buscador de lugares no está disponible". Un `503` no se reintenta solo (Nominatim admite 1
     request por segundo).
   - `useDebounce` genérico en `src/hooks/`.
   - Nominatim no priorizaba Argentina ("Córdoba" empezaba por España y "San Martín" por Países
     Bajos). **Resuelto en el backend** con `NOMINATIM_VIEWBOX` (por defecto, la caja de Argentina):
     se manda sin `bounded`, así los lugares de Argentina salen primero pero "Montevideo" se sigue
     encontrando. `NOMINATIM_COUNTRYCODES` queda para restringir del todo.
7. ~~Juntar mapa y lista en `/explorar`, alimentados por la misma búsqueda.~~ **Hecho**
   (`pages/Explorar.jsx`):
   - `useBusquedaEventos(viewport, filtros, { habilitada: viewport !== null })`: el viewport lo da
     `MapaEventos` al montarse y después de cada movimiento; mapa y lista muestran lo mismo.
     Mientras no hay viewport, la lista muestra el esqueleto (`cargando` es `isPending`).
   - Desde 1024px, panel (título, buscador, filtros y lista, con su propio scroll) y mapa lado a
     lado. Más chico, un botón flotante alterna "Mapa" / "Lista"; con el mapa a la vista, el
     buscador y los filtros quedan arriba y el mapa ocupa el resto de la pantalla. Con la lista, el
     mapa sigue montado (oculto y con tamaño real) para que su viewport siga valiendo.
   - `useEstadoExplorar()` guarda en la URL la posición del mapa (`?lat=&lng=&zoom=`) y la vista
     del celular (`?vista=mapa`), con `replace`. Al volver de la ficha con "atrás", el mapa abre
     donde estaba y no se pide de nuevo la ubicación (`useUbicacionInicial({ activo: false })`).
   - Sin ubicación del usuario (RF-03.8): aviso que se puede cerrar ("No tenemos permiso para ver tu
     ubicación: te mostramos *Buenos Aires*…") y buscador destacado. Se van al elegir un lugar.
     Si el usuario acepta el permiso tarde y todavía no movió el mapa ni buscó, se lo lleva a su
     ubicación.
   - Al elegir un lugar en `BuscadorLugar`, `fitBounds` con su recuadro (hasta zoom 16, para que
     una dirección no quede demasiado cerca).
   - `MapaEventos` suma `onInteraccion`, el centro y el zoom en `onCambioViewport`, y "50 de 120 en
     el mapa" cuando hay más resultados que los cargados. `ListaEventos` con `porZona` dice "No hay
     eventos en esta zona" y sugiere mover el mapa.
   - Probado con permiso concedido, denegado, sin respuesta y aceptado tarde, en 390, 820, 1280 y
     1920 px, en modo claro y oscuro.
8. ~~Probar el flujo rechazando el permiso de ubicación (RF-03.8).~~ **Hecho.** Casos probados en
   el navegador:
   | Caso | Resultado |
   |---|---|
   | Permiso denegado | El mapa abre en la ubicación por defecto con eventos, sin esperar el tope de 8 s, con el aviso "No tenemos permiso para ver tu ubicación…" y el buscador destacado |
   | Navegador sin geolocalización | Igual, con "Tu navegador no comparte la ubicación" |
   | Posición no disponible (GPS apagado) | Igual, con "No pudimos obtener tu ubicación" |
   | Además falla `GET /config/ubicacion-default` | Usa el respaldo fijo (Buenos Aires) |
   | Nominatim caído (`503`) | El buscador lo dice; el mapa se sigue moviendo a mano y busca eventos |
   | Elegir un lugar (escritorio y celular) | El mapa va al lugar; el aviso y el destacado se van |
   | Recargar | Abre donde estaba (la URL tiene la posición) y no muestra el aviso |
   | Entrar de nuevo a `/explorar` sin parámetros | Vuelve a pedir la ubicación y muestra el aviso |

   Ajustes que salieron de las pruebas:
   - Con el mapa a la vista en el celular, el aviso ocupaba cuatro renglones (en 320×568 quedaban
     235 px de mapa). Ahora muestra una versión corta: "Sin tu ubicación: te mostramos *Buenos
     Aires*."
   - Al cerrar el aviso con el teclado, el foco pasa al buscador en vez de perderse. Con el mouse
     o el dedo no, para no abrir el teclado del celular. `BuscadorLugar` acepta `ref` (el input).

9. ~~Diferenciar los eventos del equipo (RF-05.2).~~ **Hecho:** `BadgeEquipo` en
   `features/eventos/components/` muestra "Equipo de la plataforma" si `origen === 'SEED_EQUIPO'` y
   nada en los demás. Se usa en `TarjetaEvento` (antes de las categorías) y en `DetalleEvento`
   (junto a los estados, arriba del título).

### Etapa 3 · Organizador (CU-04 y CU-03) (hecha)
Cierra **RF-01.6**, **RF-01.7**, **RF-02.1** a **RF-02.5** y **RF-04.2**. B-1 ya está resuelto (`GET /auth/me`).
1. ~~`services/organizadores.js` y la página de solicitud.~~ **Hecho:** `pages/SolicitudOrganizador.jsx`
   decide qué mostrar según `user.organizador.estado`: el formulario (`FormularioSolicitud` en
   `features/organizadores/`) sin perfil o con uno `RECHAZADO` (con un aviso y el nombre anterior
   cargado); "en revisión" si está `PENDIENTE`; un aviso si está `SUSPENDIDO`, y "Ya sos organizador"
   con enlaces a crear evento y mis eventos si está `APROBADO` (solo se llega escribiendo la URL).
   Al enviar se llama a `refrescarUsuario()` y la página pasa sola a "Enviamos tu solicitud". Ante un
   `409` o `403` también se refresca, porque el estado cambió en otra pestaña. Con la solicitud
   pendiente, al entrar se vuelve a pedir el usuario, así una aprobación se ve sin recargar.
   El backend acepta textos vacíos y no limita la descripción: se valida en el navegador (nombre de
   hasta 255 caracteres, que es el largo de la columna; descripción de hasta 1000).
   `refrescarUsuario` pasó a ser estable (`useCallback`) para usarlo en efectos.
2. ~~`OrganizadorRoute`.~~ **Hecho:** `routes/OrganizadorRoute.jsx`, ruta contenedora dentro de `Layout`
   (el usuario ya está cargado por `PrivateRoute`). En vez de una página de "sin permiso", redirige a
   `/organizador/solicitud` con `state.requiereOrganizador`: esa página ya explica cada caso (sin
   perfil, pendiente, rechazado o suspendido) y suma un aviso de por qué se llegó ahí.
3. ~~`SelectorUbicacion` (reutiliza `Mapa` y `BuscadorLugar`).~~ **Hecho:** en `features/ubicacion/components/`.
   Controlado (`valor` = `{ latitud, longitud }` o `null`, `onCambiar(punto, { lugar })`, `error`); el
   formulario arma el `lugar` de la API. Se marca con un clic, arrastrando el pin o con el buscador:
   si el resultado es un punto (recuadro de menos de ~500 m: una dirección, un local) pone el pin ahí
   y pasa el `lugar` encontrado (para sugerir la dirección); si es una zona (barrio, ciudad) solo
   acerca el mapa. Con teclado: flechas para mover el mapa y "Marcar el centro del mapa", con una
   mira visible mientras el mapa tiene el foco. Las coordenadas se normalizan a -180..180 y se
   redondean a 6 decimales. Sin valor inicial abre en la ubicación del usuario o la por defecto
   (`useUbicacionInicial`); con valor (edición), en el punto. La rueda del mouse hace zoom, como en el
   resto de los mapas. Se puede probar suelto en `/dev/componentes`.
4. ~~`FormularioEvento` (reutiliza `SelectorCategorias`) y la página de alta.~~ **Hecho:**
   `FormularioEvento` (`features/eventos/components/`) sirve para el alta y la edición: recibe `inicial`
   (el evento de la API) y llama a `onEnviar(datos)` con el cuerpo completo; la edición lo va a
   comparar con `inicial` para mandar solo lo que cambió. Tres secciones: el evento (título,
   descripción, categorías), cuándo y cuánto (inicio, fin, precio) y dónde (`SelectorUbicacion`,
   nombre del lugar y dirección). Al elegir un resultado puntual en el buscador, completa nombre y
   dirección si están vacíos ("1500, Avenida Corrientes, ..." → "Avenida Corrientes 1500"), sin pisar
   lo que escribió el usuario. Después de un envío con errores, lleva la vista al primero.
   Las fechas se escriben en la hora de la plataforma (`ZONA_HORARIA`), la misma con la que se
   muestran; si el navegador está en otra zona, el campo lo aclara. `FormField` suma la prop `ayuda`
   (texto bajo el control, enlazado con `aria-describedby`).
   `pages/CrearEvento.jsx` publica con `crearEvento()` (el backend lo deja `PUBLICADO`), invalida la
   caché de eventos y va a la ficha reemplazando el formulario en el historial, con un aviso de
   "Publicaste el evento".
5. ~~"Mis eventos" con `BadgeEstado`.~~ **Hecho:** `pages/MisEventos.jsx` con `useMisEventos` (clave
   `clavesEventos.mios`, que se invalida junto con las demás de eventos). Separa "Próximos" (el más
   cercano primero) de "Finalizados" (el más reciente primero). Cada evento es una `FilaMiEvento`: se
   ve como `TarjetaEvento`, con `BadgeEstado` adelante (`Borrador`, `Publicado`, `Cancelado`, `Oculto`,
   y `Finalizado` para un publicado que ya terminó). El título es el enlace a la ficha y cubre la
   fila, así las acciones del paso 6 pueden ser botones aparte (`children`). Un `OCULTO` no tiene
   enlace (su ficha da 404 también para el dueño) y explica que lo ocultó un administrador. Estado
   vacío con "Crear evento"; con eventos, el botón va en el encabezado (en el celular ya está en la
   barra).
6. ~~Edición (mismo `FormularioEvento`) y cancelación.~~ **Hecho:** `permisosSobre(evento, usuario)`
   (`features/eventos/permisos.js`) decide qué se ofrece: editar si es propio y está en `BORRADOR` o
   `PUBLICADO` (aunque haya terminado, para corregir datos); cancelar, además, si no terminó.
   `pages/EditarEvento.jsx` carga el evento con `useEvento`, explica si no se puede editar (ajeno,
   cancelado u oculto) y manda en el PATCH solo lo que cambió (`cambiosEntre` en
   `cambiosEvento.js`: fechas al minuto, precio como número, lugar completo si cambió algo,
   categorías sin importar el orden); sin cambios, vuelve a la ficha sin llamar a la API.
   `BotonCancelarEvento` abre un `ConfirmDialog` → `cancelarEvento()` e invalida la caché de eventos.
   Las acciones están en las filas de "Mis eventos" (íconos) y en la ficha, para su organizador.
   La ficha muestra el aviso que le pase la página anterior (`state.aviso`): "Publicaste el evento",
   "Guardaste los cambios".
   Pendiente del backend, solo con SQLite: un PATCH que cambia una sola de las dos fechas de un
   evento con fin responde 500, porque `EditarEvento._reprogramar` compara la fecha guardada (SQLite
   la devuelve sin zona) con la nueva (con zona). Con PostgreSQL no pasa.

### Etapa 4 · Administración
Cierra **RF-05.1**, más **RF-05.5** como recomendado.
1. `AdminRoute`.
2. Botón "Ocultar evento" en el detalle.
3. Página `/admin/organizadores`.

### Etapa 5 · Cierre
1. Tests con Vitest + Testing Library: `useFormSubmit`, `useBusquedaEventos`, `useUbicacionInicial`
   y los formularios. `planning.md` prevé Vitest en el CI.
2. Agregar el build y los tests del frontend al pipeline de GitHub Actions.
3. Configuración de producción: `VITE_API_URL`, y frontend y backend bajo el mismo dominio para que
   la cookie del refresh token (`SameSite=lax`) siga funcionando.
4. Completar el README con la arquitectura del frontend.

---

## Mapa de rutas

Las rutas con sesión se renderizan dentro de `Layout` (barra de navegación + contenido). La
columna **Hoy** indica qué se muestra en este momento.

| Ruta | Página | Acceso | Etapa | Hoy |
|---|---|---|---|---|
| `/ingresar` | Login | Pública (redirige si ya hay sesión) | 0 | Hecha |
| `/registro` | Registro | Pública | 1 | Hecha |
| `/` | Redirige a `/explorar` | — | 1 | Hecha |
| `/explorar` | Mapa + lista + filtros + buscador de lugar | Usuario logueado | 2 | Hecha |
| `/eventos/:id` | Ficha de detalle | Usuario logueado | 2 | Hecha |
| `/perfil` | Datos de la cuenta, roles y "Cerrar sesión" | Usuario logueado | 1 | Hecha |
| `/organizador/solicitud` | Solicitud de perfil de organizador | Usuario logueado | 3 | Hecha |
| `/mis-eventos` | Mis eventos | Organizador aprobado | 3 | Hecha |
| `/eventos/nuevo` | Alta de evento | Organizador aprobado | 3 | Hecha |
| `/eventos/:id/editar` | Edición de evento | Organizador aprobado (dueño) | 3 | Hecha |
| `/admin/organizadores` | Solicitudes de organizador | Administrador | 4 | `EnConstruccion` (sin `AdminRoute`) |
| `/dev/componentes` | Catálogo de `components/ui` | Usuario logueado, **solo en desarrollo** | 1 | Hecha |
| `*` | No encontrado | Pública (con sesión, dentro de `Layout`) | 1 | Hecha |

`EnConstruccion` (`src/pages/EnConstruccion.jsx`) es una página provisoria con un aviso de
"Próximamente", para que los ítems de la barra no lleven a una página en blanco. Al hacer cada
página, reemplazarla en `App.jsx`.

## Componentes por ubicación

| Carpeta | Componentes |
|---|---|
| `components/ui/` (genéricos) | Hechos: `Button`, `Input`, `PasswordInput`, `Textarea`, `Select`, `FormField`, `FormError`, `SubmitButton`, `Spinner`, `Badge`, `EmptyState`, `ConfirmDialog`, `Icono`, `Avatar` |
| `components/layout/` | Hechos: `Layout`, `BarraNavegacion`, `MenuCuenta` |
| `components/mapa/` | Hechos: `Mapa` (base de Leaflet, la usan descubrimiento y organizador), `MapaUbicacion`, `iconoMarcador` |
| `routes/` | Hechos: `PrivateRoute`, `OrganizadorRoute`. Falta: `AdminRoute` |
| `features/auth/` | Hechos: `Login`, `Registro` |
| `features/eventos/` | Hechos: `ListaEventos`, `TarjetaEvento`, `BadgeEquipo`, `PanelFiltros`, `SelectorCategorias`, `useBusquedaEventos`, `useFiltrosBusqueda`, `useCategorias`, `useEvento`, `clavesEventos`, `formato`, `MapaEventos`, `useEstadoExplorar`, `FormularioEvento`, `BadgeEstado`, `FilaMiEvento`, `useMisEventos`, `BotonCancelarEvento`, `permisos`, `cambiosEvento` |
| `features/ubicacion/` | Hechos: `BuscadorLugar`, `useUbicacionInicial`, `SelectorUbicacion` |
| `features/organizadores/` | Hecho: `FormularioSolicitud`. Falta: panel de administración |
| `pages/` | Una página por ruta del mapa de rutas: arma los componentes de `features/`. Hechas: `Explorar`, `DetalleEvento`, `Perfil`, `SolicitudOrganizador`, `CrearEvento`, `MisEventos`, `EditarEvento`, `NoEncontrado`, `EnConstruccion` (provisoria) y `CatalogoComponentes` (solo desarrollo) |
| `services/` | Hechos: `client`, `auth`, `eventos`, `categorias`, `configuracion`, `geocodificacion`, `organizadores` (solicitud; falta lo de admin en la etapa 4) |
