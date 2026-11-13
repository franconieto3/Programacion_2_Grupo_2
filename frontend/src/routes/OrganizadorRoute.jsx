import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../features/auth/context/AuthContext'

// Ruta contenedora para lo que solo puede hacer un organizador APROBADO
// (RF-01.7): crear, editar y listar sus eventos. Va dentro de PrivateRoute,
// así que el usuario ya está cargado.
// Al resto lo manda a la solicitud de organizador, que explica su caso (sin
// perfil, pendiente o suspendido). El backend igual responde 403: esto es para
// no ofrecer un formulario que va a fallar al enviarlo.
const OrganizadorRoute = () => {
  const { user } = useAuth()

  if (user.organizador?.estado !== 'APROBADO') {
    // requiereOrganizador: la solicitud muestra un aviso de por qué se llegó ahí.
    return <Navigate to="/organizador/solicitud" state={{ requiereOrganizador: true }} replace />
  }
  return <Outlet />
}

export default OrganizadorRoute
