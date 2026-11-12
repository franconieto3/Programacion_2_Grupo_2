import { createContext, useContext, useEffect, useState } from 'react'
import {
  cerrarSesion,
  iniciarSesion,
  obtenerUsuarioActual,
  restaurarSesion,
} from '../../../services/auth'
import { onSesionExpirada } from '../../../services/client'

const AuthContext = createContext(null)

export const AuthContextProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true) // solo la verificación inicial

  // Al cargar la app se intenta recuperar la sesión con la cookie del refresh token.
  // Si después la sesión vence y no se puede renovar, client.js avisa y se limpia el usuario.
  useEffect(() => {
    onSesionExpirada(() => setUser(null))
    restaurarSesion()
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setLoading(false))
  }, [])

  const login = async (email, password) => {
    const usuario = await iniciarSesion({ email, password })
    setUser(usuario)
    return usuario
  }

  const logout = async () => {
    try {
      await cerrarSesion()
    } finally {
      setUser(null)
    }
  }

  // Vuelve a pedir el usuario cuando cambian sus roles sin un nuevo login
  // (p. ej. después de enviar la solicitud de organizador).
  const refrescarUsuario = async () => {
    const usuario = await obtenerUsuarioActual()
    setUser(usuario)
    return usuario
  }

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
