import { BrowserRouter, Routes, Route } from 'react-router-dom'
import PrivateRoute from './routes/PrivateRoute';
import './App.css'
import { AuthContextProvider } from './features/auth/context/AuthContext';

import { Login } from './features/auth/components/Login';
import { Registro } from './features/auth/components/Registro';
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
                <Route path="/explorar" element={<h1>Bienvenido</h1>}/>
                {/* las rutas privadas van acá */}
              </Route>
          </Routes>
        </BrowserRouter>
      </AuthContextProvider>
    </>
  )
}

export default App
