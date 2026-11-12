import { Outlet } from "react-router-dom";
import BarraNavegacion from "./BarraNavegacion";
import "./Layout.css";

// Estructura de las páginas con sesión: la barra de navegación y el contenido.
// Como ruta contenedora (dentro de PrivateRoute) muestra la ruta hija en
// <Outlet />; también se puede usar directo con `children` (p. ej. la 404).
const Layout = ({ children }) => (
  <div className="layout">
    <BarraNavegacion />
    <main className="layout-contenido">{children ?? <Outlet />}</main>
  </div>
);

export default Layout;
