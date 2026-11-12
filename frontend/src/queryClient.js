import { QueryClient } from '@tanstack/react-query'
import { ApiError } from './services/client'

// Caché única de los datos del servidor (TanStack Query). Las consultas llaman
// a las funciones de services/, así que token, renovación de sesión y ApiError
// siguen resueltos en client.js.

const MAX_REINTENTOS = 2

// Solo se reintenta lo que puede andar en un segundo intento: fallas de red y
// errores 5xx. Un 4xx (404, 403, 422...) va a dar lo mismo, y el 401 ya lo
// maneja client.js renovando la sesión.
function reintentar(intentos, error) {
  if (error instanceof ApiError && error.status < 500) return false
  return intentos < MAX_REINTENTOS
}

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Durante 30 s un dato se considera actual: volver a una pantalla no
      // dispara otra request. Las consultas que cambian poco (categorías)
      // definen su propio staleTime.
      staleTime: 30_000,
      retry: reintentar,
    },
    mutations: {
      // Una mutación repetida puede duplicar el efecto (p. ej. crear dos eventos).
      retry: false,
    },
  },
})
