// Endpoints de /auth del backend (app/auth/router.py).

import { api, renovarSesion, setAccessToken } from './client'

// datos: { email, password, nombre, apellido }. Devuelve el usuario creado,
// pero no inicia sesión: después hay que llamar a iniciarSesion().
export function registrar(datos) {
  return api.post('/auth/register', datos, { auth: false })
}

// Guarda el access token en el cliente (el refresh token queda en una cookie
// httpOnly) y devuelve { id, email, nombre, apellido }.
export async function iniciarSesion({ email, password }) {
  const { access_token, usuario } = await api.post(
    '/auth/login',
    { email, password },
    { auth: false },
  )
  setAccessToken(access_token)
  return usuario
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
// y devuelve { usuario_id, email }; si no, devuelve null.
export async function restaurarSesion() {
  const sesion = await renovarSesion()
  return sesion && { usuario_id: sesion.usuario_id, email: sesion.email }
}

// El backend responde el mismo mensaje exista o no el email.
export function recuperarContrasena(email) {
  return api.post('/auth/recover-password', { email }, { auth: false })
}
