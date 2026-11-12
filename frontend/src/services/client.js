// Cliente HTTP único del frontend: es el único módulo que usa fetch.
// Se encarga de la URL base, el access token, la renovación de sesión ante un 401
// y de convertir las respuestas de error del backend en ApiError.

const BASE_URL = import.meta.env.VITE_API_URL ?? '/api'

// El access token vive solo en memoria (no en localStorage) para que un script
// inyectado no pueda leerlo. Al recargar la página se recupera con la cookie del
// refresh token, ver restaurarSesion() en auth.js.
let accessToken = null
let alExpirarSesion = null
let renovacionEnCurso = null

export class ApiError extends Error {
  constructor(status, mensaje, detalle) {
    super(mensaje)
    this.name = 'ApiError'
    this.status = status
    this.detalle = detalle
  }
}

export function setAccessToken(token) {
  accessToken = token
}

export function haySesion() {
  return accessToken !== null
}

// Callback para cuando la sesión vence y no se puede renovar (p. ej. redirigir al login).
export function onSesionExpirada(callback) {
  alExpirarSesion = callback
}

function construirUrl(ruta, query) {
  const params = new URLSearchParams()
  for (const [clave, valor] of Object.entries(query ?? {})) {
    if (valor === undefined || valor === null || valor === '') continue
    // Las listas se mandan repitiendo el parámetro (?categorias=bar&categorias=teatro),
    // que es como las espera FastAPI.
    for (const item of Array.isArray(valor) ? valor : [valor]) {
      params.append(clave, item)
    }
  }
  const qs = params.toString()
  return `${BASE_URL}${ruta}${qs ? `?${qs}` : ''}`
}

// FastAPI devuelve {"detail": "mensaje"} en los errores del dominio y
// {"detail": [{loc, msg, ...}]} en los de validación (422).
async function crearError(respuesta) {
  const cuerpo = await respuesta.json().catch(() => null)
  const detalle = cuerpo?.detail
  let mensaje
  if (typeof detalle === 'string') {
    mensaje = detalle
  } else if (Array.isArray(detalle)) {
    mensaje = detalle.map((error) => error.msg).join('. ')
  } else {
    mensaje = `Error ${respuesta.status} al comunicarse con el servidor.`
  }
  return new ApiError(respuesta.status, mensaje, detalle)
}

// Pide un access token nuevo usando la cookie httpOnly del refresh token.
// Va sin header Authorization a propósito: si se manda el token vencido, el
// backend lo rechaza en vez de usar la cookie. Si varias requests reciben un 401
// a la vez, todas esperan la misma renovación.
export function renovarSesion() {
  renovacionEnCurso ??= (async () => {
    try {
      const respuesta = await fetch(`${BASE_URL}/auth/verify-session`, {
        method: 'POST',
        credentials: 'include',
      })
      if (!respuesta.ok) {
        accessToken = null
        return null
      }
      const sesion = await respuesta.json()
      accessToken = sesion.access_token
      return sesion
    } finally {
      renovacionEnCurso = null
    }
  })()
  return renovacionEnCurso
}

// opciones.auth = false para las rutas públicas (login, registro...): no se manda
// el token y un 401 no dispara la renovación de sesión.
// opciones.signal (AbortSignal) cancela la request. TanStack Query pasa uno a
// cada consulta y lo activa cuando la respuesta ya no hace falta (cambió la
// búsqueda o se desmontó el componente); la promesa se rechaza con un
// AbortError, que TanStack Query ignora.
export async function request(
  ruta,
  { method = 'GET', body, query, auth = true, signal } = {},
) {
  const enviar = () => {
    const headers = {}
    if (body !== undefined) headers['Content-Type'] = 'application/json'
    if (auth && accessToken) headers.Authorization = `Bearer ${accessToken}`
    return fetch(construirUrl(ruta, query), {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
      credentials: 'include',
      signal,
    })
  }

  let respuesta = await enviar()

  if (respuesta.status === 401 && auth) {
    const sesion = await renovarSesion()
    if (!sesion) {
      alExpirarSesion?.()
      throw await crearError(respuesta)
    }
    respuesta = await enviar()
  }

  if (!respuesta.ok) throw await crearError(respuesta)
  if (respuesta.status === 204) return null
  return respuesta.json()
}

export const api = {
  get: (ruta, opciones) => request(ruta, { ...opciones, method: 'GET' }),
  post: (ruta, body, opciones) => request(ruta, { ...opciones, method: 'POST', body }),
  patch: (ruta, body, opciones) => request(ruta, { ...opciones, method: 'PATCH', body }),
  delete: (ruta, opciones) => request(ruta, { ...opciones, method: 'DELETE' }),
}
