import { Outlet } from "react-router-dom";
import BarraNavegacion from "./BarraNavegacion";
import "./Layout.css";

// Estructura de las páginas con sesión: la barra de navegación y el contenido
// de la ruta actual. Se usa como ruta contenedora dentro de PrivateRoute.
const Layout = () => (
  <div className="layout">
    <BarraNavegacion />
    <main className="layout-contenido">
      <Outlet />
    </main>
  </div>
);

export default Layout;
