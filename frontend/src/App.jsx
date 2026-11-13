import { lazy, Suspense } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import PrivateRoute from './routes/PrivateRoute';
import OrganizadorRoute from './routes/OrganizadorRoute';
import { AuthContextProvider } from './features/auth/context/AuthContext';
import Layout from './components/layout/Layout';

import { Login } from './features/auth/components/Login';
import { Registro } from './features/auth/components/Registro';
import Spinner from './components/ui/Spinner';
import EnConstruccion from './pages/EnConstruccion';
import Perfil from './pages/Perfil';
import Explorar from './pages/Explorar';
import DetalleEvento from './pages/DetalleEvento';
import NoEncontrado from './pages/NoEncontrado';
import SolicitudOrganizador from './pages/SolicitudOrganizador';

// Catálogo de componentes solo en desarrollo: en el build de producción
// import.meta.env.DEV es false y Vite descarta la ruta y el import.
const CatalogoComponentes = import.meta.env.DEV
  ? lazy(() => import('./pages/CatalogoComponentes'))
  : null;

function App() {

  return (
    <>
      <AuthContextProvider>
        <BrowserRouter>
          <Routes>
              {/* Sin sesión, PrivateRoute manda de /explorar a /ingresar. */}
              <Route path="/" element={<Navigate to="/explorar" replace />} />
              <Route path="/ingresar" element={<Login />}/>
              <Route path="/registro" element={<Registro/>}/>
              <Route element={<PrivateRoute />}>
                {/* Las rutas privadas van dentro de Layout (barra de navegación + contenido).
                    Las que usan EnConstruccion se reemplazan en su etapa de la hoja de ruta. */}
                <Route element={<Layout />}>
                  <Route path="/explorar" element={<Explorar />} />
                  <Route path="/eventos/:idEvento" element={<DetalleEvento />} />
                  {/* Solo organizadores aprobados (RF-01.7). */}
                  <Route element={<OrganizadorRoute />}>
                    <Route
                      path="/mis-eventos"
                      element={
                        <EnConstruccion
                          titulo="Mis eventos"
                          icono="calendar_month"
                          descripcion="Acá vas a ver los eventos que publicaste, con su estado, y vas a poder editarlos o cancelarlos."
                        />
                      }
                    />
                    <Route
                      path="/eventos/nuevo"
                      element={
                        <EnConstruccion
                          titulo="Crear evento"
                          icono="add_location_alt"
                          descripcion="Acá vas a poder publicar un evento: datos, categorías y ubicación en el mapa."
                        />
                      }
                    />
                  </Route>
                  <Route path="/organizador/solicitud" element={<SolicitudOrganizador />} />
                  <Route
                    path="/admin/organizadores"
                    element={
                      <EnConstruccion
                        titulo="Administración"
                        icono="admin_panel_settings"
                        descripcion="Acá vas a poder aprobar, rechazar y suspender solicitudes de organizador."
                      />
                    }
                  />
                  <Route path="/perfil" element={<Perfil />} />
                  {CatalogoComponentes && (
                    <Route
                      path="/dev/componentes"
                      element={
                        <Suspense fallback={<Spinner pantallaCompleta />}>
                          <CatalogoComponentes />
                        </Suspense>
                      }
                    />
                  )}
                </Route>
              </Route>
              {/* Fuera de PrivateRoute: decide ella sola si va con layout o sin. */}
              <Route path="*" element={<NoEncontrado />} />
          </Routes>
        </BrowserRouter>
      </AuthContextProvider>
    </>
  )
}

export default App
