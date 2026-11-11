// Endpoints de /eventos del backend (app/eventos/router.py y admin_router.py).
// Todos requieren sesión iniciada.

import { api } from './client'

// filtros (todos opcionales):
//   lat_min, lat_max, lng_min, lng_max  viewport del mapa: los cuatro o ninguno
//   desde, hasta                        fechas 'YYYY-MM-DD'
//   hora_desde, hora_hasta              'HH:MM'
//   categorias                          lista de slugs, p. ej. ['bar', 'teatro']
//   limit (1-100, default 20), offset   paginación
// Devuelve { items, total, limit, offset }.
export function buscarEventos(filtros = {}) {
  return api.get('/eventos', { query: filtros })
}

export function obtenerEvento(idEvento) {
  return api.get(`/eventos/${idEvento}`)
}

// Solo organizadores aprobados: sus eventos en cualquier estado.
export function listarMisEventos() {
  return api.get('/eventos/mios')
}

export function crearEvento(datos) {
  return api.post('/eventos', datos)
}

// cambios: solo los campos a modificar.
export function editarEvento(idEvento, cambios) {
  return api.patch(`/eventos/${idEvento}`, cambios)
}

export function cancelarEvento(idEvento) {
  return api.post(`/eventos/${idEvento}/cancelar`)
}

// Solo administradores (moderación).
export function ocultarEvento(idEvento) {
  return api.post(`/admin/eventos/${idEvento}/ocultar`)
}
