import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import {
  cerrarSesion,
  iniciarSesion,
  obtenerUsuarioActual,
  restaurarSesion,
} from '../../../services/auth'
import { onSesionExpirada } from '../../../services/client'
import { useQueryClient } from '@tanstack/react-query'

const AuthContext = createContext(null)

export const AuthContextProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true) // solo la verificación inicial
  const queryClient = useQueryClient()

  // Al salir de la sesión se vacía la caché de TanStack Query, para que el
  // próximo usuario en este navegador no vea datos del anterior (p. ej. "Mis eventos").
  const limpiarSesion = useCallback(() => {
    setUser(null)
    queryClient.clear()
  }, [queryClient])

  // Al cargar la app se intenta recuperar la sesión con la cookie del refresh token.
  // Si después la sesión vence y no se puede renovar, client.js avisa y se limpia el usuario.
  // queryClient es único (queryClient.js), así que limpiarSesion no cambia y esto
  // corre una sola vez.
  useEffect(() => {
    onSesionExpirada(limpiarSesion)
    restaurarSesion()
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setLoading(false))
  }, [limpiarSesion])

  const login = async (email, password) => {
    const usuario = await iniciarSesion({ email, password })
    setUser(usuario)
    return usuario
  }

  const logout = async () => {
    try {
      await cerrarSesion()
    } finally {
      limpiarSesion()
    }
  }

  // Vuelve a pedir el usuario cuando cambian sus roles sin un nuevo login
  // (p. ej. después de enviar la solicitud de organizador). Es estable entre
  // renders, así se puede usar como dependencia de un efecto.
  const refrescarUsuario = useCallback(async () => {
    const usuario = await obtenerUsuarioActual()
    setUser(usuario)
    return usuario
  }, [])

  return (
    <AuthContext.Provider
      value={{ user, isAuthenticated: !!user, loading, login, logout, refrescarUsuario }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth tiene que usarse dentro de AuthContextProvider')
  return ctx
}
