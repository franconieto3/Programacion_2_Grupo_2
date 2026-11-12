import { Link, NavLink } from "react-router-dom";
import { useAuth } from "../../features/auth/context/AuthContext";
import Avatar from "../ui/Avatar";
import Icono from "../ui/Icono";
import MenuCuenta from "./MenuCuenta";
import "./BarraNavegacion.css";

// Nombre provisorio del producto (planning.md, pendiente 7).
export const NOMBRE_APP = "Eventos";

// Ítems según los roles del usuario (GET /auth/me). El backend igual valida
// cada acción: esto es para no ofrecer lo que va a responder 403.
// `ordenMovil` acomoda la barra inferior del celular, donde "Crear" va al medio.
function itemsPara(user) {
  const esOrganizador = user.organizador?.estado === "APROBADO";
  return [
    { a: "/explorar", texto: "Explorar", icono: "explore", ordenMovil: 1 },
    esOrganizador && {
      a: "/mis-eventos",
      texto: "Mis eventos",
      icono: "calendar_month",
      ordenMovil: 2,
    },
    !esOrganizador && {
      a: "/organizador/solicitud",
      texto: "Ser organizador",
      icono: "storefront",
      ordenMovil: 2,
    },
    user.es_admin && {
      a: "/admin/organizadores",
      texto: "Administración",
      icono: "admin_panel_settings",
      ordenMovil: 4,
    },
    { a: "/perfil", texto: "Perfil", avatar: true, ordenMovil: 5 },
    esOrganizador && {
      a: "/eventos/nuevo",
      texto: "Crear evento",
      icono: "add",
      destacado: true,
      ordenMovil: 3,
    },
  ].filter(Boolean);
}

// Navegación principal, al estilo de Instagram y X web:
// - celular: barra de pestañas fija abajo, solo íconos;
// - desde 768px: columna fija a la izquierda, solo íconos;
// - desde 1264px: la misma columna, con los textos.
// Los textos siempre están en el DOM (ocultos visualmente cuando no entran),
// así los lectores de pantalla los anuncian en todos los tamaños.
const BarraNavegacion = () => {
  const { user } = useAuth();

  return (
    <nav className="barra" aria-label="Principal">
      <Link to="/explorar" className="barra-marca">
        <Icono nombre="location_on" relleno />
        <span className="barra-marca-nombre">{NOMBRE_APP}</span>
      </Link>

      <ul className="barra-items">
        {itemsPara(user).map((item) => (
          <li
            key={item.a}
            className="barra-item"
            style={{ "--orden-movil": item.ordenMovil }}
          >
            <NavLink
              to={item.a}
              title={item.texto}
              className={({ isActive }) =>
                [
                  "barra-enlace",
                  item.destacado && "barra-enlace-destacado",
                  isActive && "barra-enlace-activo",
                ]
                  .filter(Boolean)
                  .join(" ")
              }
            >
              {({ isActive }) => (
                <>
                  {item.avatar ? (
                    <Avatar usuario={user} tamano="sm" className="barra-avatar" />
                  ) : (
                    <Icono nombre={item.icono} relleno={isActive && !item.destacado} />
                  )}
                  <span className="barra-texto">{item.texto}</span>
                </>
              )}
            </NavLink>
          </li>
        ))}
      </ul>

      <MenuCuenta />
    </nav>
  );
};

export default BarraNavegacion;
