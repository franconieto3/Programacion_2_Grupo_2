import { Navigate, Outlet, useLocation } from 'react-router-dom'
import Spinner from '../components/ui/Spinner'
import { useAuth } from '../features/auth/context/AuthContext'

// Ruta contenedora: las rutas privadas se declaran como hijas y se renderizan en <Outlet />.
const PrivateRoute = () => {
  const { user, loading } = useAuth()
  const location = useLocation()

  if (loading) return <Spinner pantallaCompleta etiqueta="Recuperando la sesión" />
  if (!user) return <Navigate to="/ingresar" state={{ from: location }} replace />
  return <Outlet />
}

export default PrivateRoute
