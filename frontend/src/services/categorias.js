// Endpoint de /categorias del backend (app/categorias/router.py).
// Público: no requiere sesión.

import { api } from './client'

// Catálogo cerrado de categorías (RF-04.1), ordenado por nombre.
// Devuelve [{ slug, nombre, descripcion }]: se muestra `nombre` y a la API se
// manda `slug` (filtros de buscarEventos() y categorías de un evento).
// El catálogo casi no cambia: la consulta que lo use tiene que definir un
// staleTime largo.
export function listarCategorias({ signal } = {}) {
  return api.get('/categorias', { auth: false, signal })
}
