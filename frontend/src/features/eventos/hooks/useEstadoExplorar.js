import { useCallback, useState } from 'react'
import { useSearchParams } from 'react-router-dom'

// Lo que /explorar guarda en la URL además de los filtros
// (useFiltrosBusqueda): dónde estaba el mapa (?lat=&lng=&zoom=) y, en el
// celular, si se veía el mapa o la lista (?vista=mapa). Así, al volver de la
// ficha de un evento con "atrás", la página queda como estaba.
//
//   const { posicionInicial, guardarPosicion, vista, cambiarVista } =
//     useEstadoExplorar()
//
// - posicionInicial: { lat, lng, zoom } leída al entrar, o null si la URL no
//   la trae (o está mal formada). No cambia mientras la página esté abierta:
//   el mapa solo usa la posición al montarse.
// - guardarPosicion({ lat, lng }, zoom): cada vez que el mapa termina de
//   moverse.
// - vista: 'lista' o 'mapa'.
//
// Todo se escribe con `replace`: mover el mapa no agrega entradas al
// historial, así "atrás" sale de la página en vez de deshacer movimientos.

const ZOOM_MIN = 3
const ZOOM_MAX = 19

export function leerPosicion(params) {
  const lat = Number(params.get('lat'))
  const lng = Number(params.get('lng'))
  const zoom = Number(params.get('zoom'))
  const valida =
    params.has('lat') &&
    params.has('lng') &&
    params.has('zoom') &&
    Number.isFinite(lat) &&
    Number.isFinite(lng) &&
    Math.abs(lat) <= 85 &&
    Math.abs(lng) <= 180 &&
    Number.isInteger(zoom) &&
    zoom >= ZOOM_MIN &&
    zoom <= ZOOM_MAX
  return valida ? { lat, lng, zoom } : null
}

export function useEstadoExplorar() {
  const [params, setParams] = useSearchParams()
  const [posicionInicial] = useState(() => leerPosicion(params))

  const actualizar = useCallback(
    (cambios) =>
      setParams(
        (anteriores) => {
          const siguientes = new URLSearchParams(anteriores)
          for (const [clave, valor] of Object.entries(cambios)) {
            if (valor === null) siguientes.delete(clave)
            else siguientes.set(clave, valor)
          }
          return siguientes
        },
        { replace: true },
      ),
    [setParams],
  )

  // 5 decimales (un metro): suficiente para volver al mismo lugar sin
  // ensuciar la URL.
  const guardarPosicion = useCallback(
    ({ lat, lng }, zoom) =>
      actualizar({ lat: lat.toFixed(5), lng: lng.toFixed(5), zoom: String(zoom) }),
    [actualizar],
  )

  const vista = params.get('vista') === 'mapa' ? 'mapa' : 'lista'
  const cambiarVista = useCallback(
    (nueva) => actualizar({ vista: nueva === 'mapa' ? 'mapa' : null }),
    [actualizar],
  )

  return { posicionInicial, guardarPosicion, vista, cambiarVista }
}
