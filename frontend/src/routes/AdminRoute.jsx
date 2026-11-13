import { Link, Outlet } from 'react-router-dom'
import EmptyState from '../components/ui/EmptyState'
import { useAuth } from '../features/auth/context/AuthContext'

const CLASES_BOTON = 'btn-base btn-variant-outline btn-size-default'

// Ruta contenedora para la administración (RF-05.1, RF-05.5): solo usuarios
// con perfil de administrador (`es_admin` de GET /auth/me). Va dentro de
// PrivateRoute y de Layout, así que el usuario ya está cargado y el aviso se
// muestra con la barra de navegación.
// A diferencia de OrganizadorRoute no redirige: el rol de administrador no se
// solicita desde la app, así que no hay una página que explique cómo
// conseguirlo. El backend igual responde 403 a quien no lo es.
const AdminRoute = () => {
  const { user } = useAuth()

  if (!user.es_admin) {
    return (
      <div className="pagina">
        <EmptyState
          icono="lock"
          titulo="Esta sección es solo para administradores"
          descripcion="Si necesitás moderar eventos o revisar solicitudes de organizador, pedíselo al equipo de la plataforma."
        >
          <Link to="/explorar" className={CLASES_BOTON}>
            Ir a Explorar
          </Link>
        </EmptyState>
      </div>
    )
  }
  return <Outlet />
}

export default AdminRoute
