import { useState } from "react";
import { Outlet } from "react-router-dom";
import BarraNavegacion from "./BarraNavegacion";
import Pie from "../brand/Pie";
import { RanuraBarraContext } from "./ranuraBarra";
import "./Layout.css";

// Estructura de las páginas con sesión: barra superior fija y el contenido.
// Como ruta contenedora (dentro de PrivateRoute) muestra la ruta hija en
// <Outlet />, seguida del footer; también se puede usar directo con
// `children` (p. ej. la 404).
// La barra expone una ranura central (ranuraBarra.js) para que la página
// ponga ahí su buscador.
const Layout = ({ children }) => {
  const [ranura, setRanura] = useState(null);

  return (
    <RanuraBarraContext.Provider value={ranura}>
      <div className="layout">
        <BarraNavegacion ranuraRef={setRanura} />
        <main className="layout-contenido">
          {children ?? <Outlet />}
          <Pie className="layout-pie" />
        </main>
      </div>
    </RanuraBarraContext.Provider>
  );
};

export default Layout;
