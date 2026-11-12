import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { obtenerUbicacionDefault } from '../../../services/configuracion'

// Dónde abrir el mapa del descubrimiento (RF-03.1, RF-03.8, flujo 3a de CU-01).
//
//   const { cargando, ubicacion, origen, motivo } = useUbicacionInicial()
//
// - Pide la ubicación del navegador y, en paralelo, la ubicación por defecto
//   del backend (GET /config/ubicacion-default).
// - ubicacion: { lat, lng, zoom, nombre }. `nombre` es null si es la del
//   usuario, y el de la ciudad si es la por defecto (para el aviso
//   "mostramos {nombre}").
// - origen: 'usuario' o 'defecto'. motivo (solo con 'defecto'): 'denegado',
//   'sin-respuesta', 'no-disponible' o 'no-soportado'.
// - cargando: true mientras no se sabe ninguna de las dos.
//
// Tope propio de `espera` ms: mientras el cartel de permiso está abierto, el
// timeout de getCurrentPosition no corre, y si el usuario no contesta el mapa
// no se abriría nunca. Al vencer se usa la ubicación por defecto; si después
// el usuario acepta, `ubicacion` cambia una vez más a la suya (la página
// recentra el mapa).

const ZOOM_USUARIO = 14
const ESPERA = 8000
const ANTIGUEDAD_MAXIMA = 5 * 60 * 1000 // sirve una posición de hasta 5 minutos

// Por si el backend tampoco responde: el mapa no puede quedar sin abrir.
// Coincide con el valor por defecto de Settings en el backend.
const RESPALDO = { lat: -34.6037, lng: -58.3816, zoom: 12, nombre: 'Buenos Aires' }

const MOTIVOS = { 1: 'denegado', 2: 'no-disponible', 3: 'sin-respuesta' }

export function useUbicacionInicial({ espera = ESPERA } = {}) {
  const defecto = useQuery({
    queryKey: ['configuracion', 'ubicacion-default'],
    queryFn: ({ signal }) => obtenerUbicacionDefault({ signal }),
    staleTime: Infinity,
  })

  const [geo, setGeo] = useState(() =>
    'geolocation' in navigator
      ? { estado: 'buscando' }
      : { estado: 'fallo', motivo: 'no-soportado' },
  )

  useEffect(() => {
    if (!('geolocation' in navigator)) return
    let vigente = true

    const tope = setTimeout(() => {
      if (vigente) {
        setGeo((actual) =>
          actual.estado === 'buscando' ? { estado: 'fallo', motivo: 'sin-respuesta' } : actual,
        )
      }
    }, espera)

    navigator.geolocation.getCurrentPosition(
      // Aunque llegue después del tope, se usa: el usuario dio el permiso.
      ({ coords }) => {
        if (!vigente) return
        clearTimeout(tope)
        setGeo({ estado: 'ok', lat: coords.latitude, lng: coords.longitude })
      },
      (error) => {
        if (!vigente) return
        clearTimeout(tope)
        setGeo({ estado: 'fallo', motivo: MOTIVOS[error.code] ?? 'no-disponible' })
      },
      { timeout: espera, maximumAge: ANTIGUEDAD_MAXIMA, enableHighAccuracy: false },
    )

    return () => {
      vigente = false
      clearTimeout(tope)
    }
  }, [espera])

  if (geo.estado === 'ok') {
    return {
      cargando: false,
      ubicacion: { lat: geo.lat, lng: geo.lng, zoom: ZOOM_USUARIO, nombre: null },
      origen: 'usuario',
      motivo: null,
    }
  }

  const porDefecto = defecto.data ?? (defecto.isError ? RESPALDO : null)
  if (geo.estado === 'buscando' || !porDefecto) {
    return { cargando: true, ubicacion: null, origen: null, motivo: null }
  }
  return { cargando: false, ubicacion: porDefecto, origen: 'defecto', motivo: geo.motivo }
}
