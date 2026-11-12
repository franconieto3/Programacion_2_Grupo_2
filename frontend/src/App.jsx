import { BrowserRouter, Routes, Route } from 'react-router-dom'
import PrivateRoute from './routes/PrivateRoute';
import { AuthContextProvider } from './features/auth/context/AuthContext';
import Layout from './components/layout/Layout';

import { Login } from './features/auth/components/Login';
import { Registro } from './features/auth/components/Registro';
import EnConstruccion from './pages/EnConstruccion';
import Perfil from './pages/Perfil';

function App() {

  return (
    <>
      <AuthContextProvider>
        <BrowserRouter>
          <Routes>
              <Route path="/" element={<Login />} />
              <Route path="/ingresar" element={<Login />}/>
              <Route path="/registro" element={<Registro/>}/>
              <Route element={<PrivateRoute />}>
                {/* Las rutas privadas van dentro de Layout (barra de navegación + contenido).
                    Las que usan EnConstruccion se reemplazan en su etapa de la hoja de ruta. */}
                <Route element={<Layout />}>
                  <Route
                    path="/explorar"
                    element={
                      <EnConstruccion
                        titulo="Explorar"
                        icono="map"
                        descripcion="Acá vas a ver el mapa y la lista de eventos cerca tuyo, con filtros por fecha, horario y categoría."
                      />
                    }
                  />
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
                  <Route
                    path="/organizador/solicitud"
                    element={
                      <EnConstruccion
                        titulo="Ser organizador"
                        icono="storefront"
                        descripcion="Acá vas a poder pedir un perfil de organizador para publicar tus propios eventos."
                      />
                    }
                  />
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
                </Route>
              </Route>
          </Routes>
        </BrowserRouter>
      </AuthContextProvider>
    </>
  )
}

export default App
