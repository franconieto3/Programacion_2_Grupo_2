// Endpoints de /config del backend (app/configuracion/router.py).
// Públicos: no requieren sesión.

import { api } from './client'

// Dónde se abre el mapa si el usuario no da permiso de geolocalización o el
// navegador no responde a tiempo (RF-03.8). Devuelve { nombre, lat, lng, zoom }:
// `zoom` es el nivel inicial del mapa (0 a 19, escala de los tiles de OSM) y
// `nombre` sirve para el aviso "mostramos {nombre}".
export function obtenerUbicacionDefault({ signal } = {}) {
  return api.get('/config/ubicacion-default', { auth: false, signal })
}
