// Endpoints de /geocodificacion del backend (app/geocodificacion/router.py).
// Requieren sesión.

import { api } from './client'

// Mínimo de caracteres que acepta el backend (con menos responde 422). El
// buscador no tiene que llamar a buscarLugar() hasta llegar a este largo.
export const MIN_CARACTERES_BUSQUEDA = 3

// Busca un lugar por texto (RF-03.7). El backend consulta Nominatim (OSM),
// que admite 1 request por segundo: las búsquedas mientras se tipea tienen que
// ir con debounce, y conviene pasar el `signal` de TanStack Query para
// cancelar las que quedan viejas.
//
// opciones: limit (1-10, default 5 en el backend), signal.
// Devuelve [{ nombre, tipo, lat, lng, lat_min, lat_max, lng_min, lng_max }]:
// el recuadro tiene los mismos nombres que el viewport de buscarEventos(),
// así se le puede pasar directo a map.fitBounds(). Sin coincidencias devuelve
// []; si Nominatim no responde, ApiError con status 503.
export function buscarLugar(texto, { limit, signal } = {}) {
  return api.get('/geocodificacion/buscar', {
    query: { q: texto.trim(), limit },
    signal,
  })
}
