import { Link, NavLink } from "react-router-dom";
import { useAuth } from "../../features/auth/context/AuthContext";
import Logo from "../brand/Logo";
import { NOMBRE_APP } from "../brand/marca";
import Icono from "../ui/Icono";
import MenuCuenta from "./MenuCuenta";
import { permisosDe } from "./permisos";
import "./BarraNavegacion.css";

// Se mantiene el export por compatibilidad; la fuente es brand/marca.js.
export { NOMBRE_APP };

const claseAccion = (variante) => ({ isActive }) =>
  [
    "btn-base",
    `btn-variant-${variante}`,
    "btn-size-default",
    "barra-accion",
    isActive && "barra-accion-activa",
  ]
    .filter(Boolean)
    .join(" ");

// Barra superior (map-first, al estilo de Airbnb / Google Maps):
// - izquierda: logo (lleva a Explorar);
// - centro: la ranura donde la página pone su buscador (Explorar lo usa para
//   mover el mapa). En las demás páginas hay un atajo con forma de buscador
//   que lleva a Explorar;
// - derecha: "Ser organizador" o "Crear evento" y el menú de la cuenta
//   (Perfil, Mis eventos, Administración, Cerrar sesión).
// En el celular las acciones de la derecha pasan al menú de la cuenta.
const BarraNavegacion = ({ ranuraRef }) => {
  const { user } = useAuth();
  const permisos = permisosDe(user);

  return (
    <header className="barra">
      <Link to="/explorar" className="barra-marca" aria-label={`${NOMBRE_APP}, ir a Explorar`}>
        <Logo size={32} textoClassName="barra-marca-nombre" />
      </Link>

      <div className="barra-centro">
        <div ref={ranuraRef} className="barra-ranura" />
        <Link to="/explorar" className="barra-atajo-buscar">
          <Icono nombre="search" />
          <span>Buscar eventos en el mapa</span>
        </Link>
      </div>

      <nav className="barra-acciones" aria-label="Cuenta">
        {permisos.puedeSolicitar && (
          <NavLink to="/organizador/solicitud" className={claseAccion("ghost")}>
            <Icono nombre="storefront" />
            Ser organizador
          </NavLink>
        )}
        {permisos.esOrganizador && (
          <NavLink to="/eventos/nuevo" className={claseAccion("brand")}>
            <Icono nombre="add" />
            Crear evento
          </NavLink>
        )}
        <MenuCuenta permisos={permisos} />
      </nav>
    </header>
  );
};

export default BarraNavegacion;
