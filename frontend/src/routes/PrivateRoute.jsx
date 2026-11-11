import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../features/auth/context/AuthContext'

// Ruta contenedora: las rutas privadas se declaran como hijas y se renderizan en <Outlet />.
const PrivateRoute = () => {
  const { user, loading } = useAuth()
  const location = useLocation()

  if (loading) return <div>Cargando...</div>
  if (!user) return <Navigate to="/ingresar" state={{ from: location }} replace />
  return <Outlet />
}

export default PrivateRoute
