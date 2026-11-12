// Endpoints de /auth del backend (app/auth/router.py).

import { api, renovarSesion, setAccessToken } from './client'

// datos: { email, password, nombre, apellido }. Devuelve el usuario creado,
// pero no inicia sesión: después hay que llamar a iniciarSesion().
export function registrar(datos) {
  return api.post('/auth/register', datos, { auth: false })
}

// Usuario de la sesión actual con sus roles:
// { id, email, nombre, apellido, organizador: { id_organizador, nombre_publico, estado } | null, es_admin }.
// Login y restaurarSesion() devuelven siempre esta misma forma.
export function obtenerUsuarioActual() {
  return api.get('/auth/me')
}

// Guarda el access token en el cliente (el refresh token queda en una cookie
// httpOnly) y devuelve el usuario de obtenerUsuarioActual().
export async function iniciarSesion({ email, password }) {
  const { access_token } = await api.post(
    '/auth/login',
    { email, password },
    { auth: false },
  )
  setAccessToken(access_token)
  return obtenerUsuarioActual()
}

export async function cerrarSesion() {
  try {
    await api.post('/auth/logout', undefined, { auth: false })
  } finally {
    // Aunque falle la request, en este navegador la sesión se da por cerrada.
    setAccessToken(null)
  }
}

// Llamar al cargar la app: si hay una cookie de refresh válida, recupera la sesión
// y devuelve el usuario de obtenerUsuarioActual(); si no, devuelve null.
export async function restaurarSesion() {
  const sesion = await renovarSesion()
  if (!sesion) return null
  return obtenerUsuarioActual()
}

// El backend responde el mismo mensaje exista o no el email.
export function recuperarContrasena(email) {
  return api.post('/auth/recover-password', { email }, { auth: false })
}
