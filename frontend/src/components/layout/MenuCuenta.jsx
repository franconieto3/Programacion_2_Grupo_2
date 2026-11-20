import { useEffect, useId, useRef, useState } from "react";
import { NavLink } from "react-router-dom";
import { useAuth } from "../../features/auth/context/AuthContext";
import Avatar from "../ui/Avatar";
import Icono from "../ui/Icono";

// Enlaces del menú según los permisos (permisos.js).
// `soloMovil`: en pantallas anchas ya están como botones en la barra.
function enlacesPara({ esOrganizador, puedeSolicitar, esAdmin }) {
  return [
    { a: "/perfil", texto: "Perfil", icono: "person" },
    esOrganizador && { a: "/mis-eventos", texto: "Mis eventos", icono: "calendar_month" },
    esOrganizador && { a: "/eventos/nuevo", texto: "Crear evento", icono: "add", soloMovil: true },
    puedeSolicitar && {
      a: "/organizador/solicitud",
      texto: "Ser organizador",
      icono: "storefront",
      soloMovil: true,
    },
    esAdmin && { a: "/admin/organizadores", texto: "Administración", icono: "admin_panel_settings" },
  ].filter(Boolean);
}

// Botón con el avatar a la derecha de la barra: abre un menú desplegable con
// los datos de la cuenta, los enlaces y "Cerrar sesión".
const MenuCuenta = ({ permisos }) => {
  const { user, logout } = useAuth();
  const [abierto, setAbierto] = useState(false);
  const contenedor = useRef(null);
  const boton = useRef(null);
  const idMenu = useId();

  // Se cierra con Escape (devolviendo el foco al botón) o con un clic afuera.
  useEffect(() => {
    if (!abierto) return;
    const alClic = (evento) => {
      if (!contenedor.current?.contains(evento.target)) setAbierto(false);
    };
    const alTecla = (evento) => {
      if (evento.key === "Escape") {
        setAbierto(false);
        boton.current?.focus();
      }
    };
    document.addEventListener("mousedown", alClic);
    document.addEventListener("keydown", alTecla);
    return () => {
      document.removeEventListener("mousedown", alClic);
      document.removeEventListener("keydown", alTecla);
    };
  }, [abierto]);

  const cerrar = () => setAbierto(false);

  return (
    <div className="cuenta" ref={contenedor}>
      <button
        ref={boton}
        type="button"
        className="cuenta-boton"
        aria-haspopup="menu"
        aria-expanded={abierto}
        aria-controls={abierto ? idMenu : undefined}
        aria-label={`Cuenta de ${user.nombre ?? user.email}`}
        title={user.email}
        onClick={() => setAbierto((valor) => !valor)}
      >
        <Icono nombre="menu" className="cuenta-hamburguesa" />
        <Avatar usuario={user} tamano="sm" />
      </button>

      {abierto && (
        <div className="cuenta-menu" id={idMenu} role="menu">
          <div className="cuenta-encabezado">
            <Avatar usuario={user} />
            <span className="cuenta-datos">
              <span className="cuenta-nombre">
                {user.nombre} {user.apellido}
              </span>
              <span className="cuenta-email">{user.email}</span>
            </span>
          </div>
          <div className="cuenta-separador" role="separator" />
          {enlacesPara(permisos).map((enlace) => (
            <NavLink
              key={enlace.a}
              to={enlace.a}
              role="menuitem"
              className={({ isActive }) =>
                [
                  "cuenta-menu-item",
                  enlace.soloMovil && "cuenta-menu-item-movil",
                  isActive && "cuenta-menu-item-activo",
                ]
                  .filter(Boolean)
                  .join(" ")
              }
              onClick={cerrar}
            >
              <Icono nombre={enlace.icono} />
              {enlace.texto}
            </NavLink>
          ))}
          <div className="cuenta-separador" role="separator" />
          <button
            type="button"
            role="menuitem"
            className="cuenta-menu-item cuenta-menu-salir"
            onClick={logout}
          >
            <Icono nombre="logout" />
            Cerrar sesión
          </button>
        </div>
      )}
    </div>
  );
};

export default MenuCuenta;
