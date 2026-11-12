import { useMemo } from 'react'
import { keepPreviousData, useInfiniteQuery } from '@tanstack/react-query'
import { buscarEventos } from '../../../services/eventos'
import { clavesEventos } from '../clavesEventos'

// Búsqueda de eventos del descubrimiento (CU-01). El mapa y la lista usan
// este mismo hook con los mismos argumentos, así comparten la consulta y
// nunca muestran resultados distintos (RF-03.2).
//
//   const { eventos, total, cargando, error, hayMas, cargarMas } =
//     useBusquedaEventos(viewport, filtros)
//
// viewport: { lat_min, lat_max, lng_min, lng_max } (lo que da
//   map.getBounds()) o null para buscar sin límite geográfico.
// filtros: { desde, hasta, hora_desde, hora_hasta, categorias }, todos
//   opcionales; los vacíos se ignoran.
// opciones.habilitada: false para no buscar todavía (p. ej. mientras el
//   mapa no tiene su primer viewport). opciones.tamanoPagina: default 50.
//
// No hace debounce: el que cambia el viewport (el mapa, al moverse) tiene
// que esperar a que el usuario termine. Si igual llegan cambios seguidos,
// cada búsqueda nueva cancela la anterior (el `signal` de TanStack Query).

export const TAMANO_PAGINA = 50

const DECIMALES = 1e4 // 4 decimales: unos 11 metros

export function useBusquedaEventos(
  viewport,
  filtros,
  { habilitada = true, tamanoPagina = TAMANO_PAGINA } = {},
) {
  const parametros = {
    ...normalizarFiltros(filtros),
    ...normalizarViewport(viewport),
  }

  const consulta = useInfiniteQuery({
    queryKey: clavesEventos.busqueda(parametros, tamanoPagina),
    queryFn: ({ pageParam, signal }) =>
      buscarEventos(
        { ...parametros, limit: tamanoPagina, offset: pageParam },
        { signal },
      ),
    initialPageParam: 0,
    getNextPageParam: (ultima) => {
      const siguiente = ultima.offset + ultima.limit
      return siguiente < ultima.total ? siguiente : undefined
    },
    // Al mover el mapa o cambiar un filtro se siguen mostrando los resultados
    // anteriores hasta que llegan los nuevos, en vez de vaciar el mapa y la
    // lista en cada cambio.
    placeholderData: keepPreviousData,
    enabled: habilitada,
  })

  const { data } = consulta
  const eventos = useMemo(() => unirPaginas(data?.pages), [data])

  // Mientras se muestran los resultados de la búsqueda anterior no se puede
  // pedir la página siguiente: sería la de otra búsqueda.
  const hayMas = consulta.hasNextPage && !consulta.isPlaceholderData

  return {
    eventos,
    // Cantidad de eventos que cumplen la búsqueda; `eventos` puede tener
    // menos si todavía no se pidieron todas las páginas.
    total: data?.pages.at(-1)?.total ?? 0,
    // Primera carga, todavía sin ningún resultado para mostrar.
    cargando: consulta.isPending && habilitada,
    // Hay resultados en pantalla pero se está buscando de nuevo (cambió el
    // viewport o un filtro, o se refrescan los datos).
    actualizando:
      consulta.isFetching && !consulta.isPending && !consulta.isFetchingNextPage,
    error: consulta.error,
    hayMas,
    cargarMas: () => {
      if (hayMas && !consulta.isFetchingNextPage) consulta.fetchNextPage()
    },
    cargandoMas: consulta.isFetchingNextPage,
    reintentar: () => consulta.refetch(),
  }
}

// Deja el viewport como lo acepta el backend y estable para la clave de caché.
// - Leaflet devuelve longitudes fuera de -180..180 cuando el mundo se repite
//   horizontalmente: se trasladan al rango y lo que cruza el antimeridiano se
//   recorta (el backend no acepta viewports que lo crucen).
// - Con todo el mundo a la vista (zoom muy lejano) va el mundo entero.
// - Se redondea a 4 decimales hacia afuera: movimientos de unos metros no
//   generan otra búsqueda y el recuadro nunca queda más chico que el visible.
export function normalizarViewport(viewport) {
  if (!viewport) return null
  const { lat_min, lat_max, lng_min, lng_max } = viewport

  let lngMin = -180
  let lngMax = 180
  if (lng_max - lng_min < 360) {
    const desplazamiento = Math.floor((lng_min + 180) / 360) * 360
    lngMin = lng_min - desplazamiento
    lngMax = Math.min(lng_max - desplazamiento, 180)
  }

  return {
    lat_min: hacia(Math.max(lat_min, -90), Math.floor),
    lat_max: hacia(Math.min(lat_max, 90), Math.ceil),
    lng_min: hacia(lngMin, Math.floor),
    lng_max: hacia(lngMax, Math.ceil),
  }
}

// El toFixed descarta el error de punto flotante antes de redondear hacia
// afuera (si no, -34.690000000000005 terminaría en -34.6901).
const hacia = (valor, redondeo) =>
  redondeo(Number((valor * DECIMALES).toFixed(6))) / DECIMALES

// Saca los filtros vacíos y ordena las categorías: ['teatro', 'bar'] y
// ['bar', 'teatro'] son la misma búsqueda y comparten la caché.
export function normalizarFiltros(filtros = {}) {
  const { categorias = [], ...resto } = filtros
  const normalizados = {}
  for (const clave of ['desde', 'hasta', 'hora_desde', 'hora_hasta']) {
    if (resto[clave]) normalizados[clave] = resto[clave]
  }
  if (categorias.length > 0) {
    normalizados.categorias = [...new Set(categorias)].sort()
  }
  return normalizados
}

// Junta las páginas en una sola lista. Si entre una página y la siguiente se
// publicó o canceló un evento, el corrimiento del offset puede repetir uno:
// se queda la primera aparición.
function unirPaginas(paginas = []) {
  const vistos = new Set()
  const eventos = []
  for (const evento of paginas.flatMap((pagina) => pagina.items)) {
    if (vistos.has(evento.id_evento)) continue
    vistos.add(evento.id_evento)
    eventos.push(evento)
  }
  return eventos
}
