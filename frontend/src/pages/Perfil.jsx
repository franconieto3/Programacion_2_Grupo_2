import { Link } from "react-router-dom";
import Avatar from "../components/ui/Avatar";
import Badge from "../components/ui/Badge";
import Button from "../components/ui/Button";
import Icono from "../components/ui/Icono";
import { useAuth } from "../features/auth/context/AuthContext";
import "./Perfil.css";

const ESTADO_ORGANIZADOR = {
  PENDIENTE: { texto: "Pendiente", variante: "advertencia" },
  APROBADO: { texto: "Aprobado", variante: "exito" },
  RECHAZADO: { texto: "Rechazado", variante: "error" },
  SUSPENDIDO: { texto: "Suspendido", variante: "error" },
};

// Datos de la cuenta y sus roles. Todavía no se pueden editar (RF-01.4 no
// tiene endpoint). En el celular es además el lugar para cerrar sesión.
const Perfil = () => {
  const { user, logout } = useAuth();
  const { organizador } = user;

  return (
    <div className="pagina">
      <header className="perfil-encabezado">
        <Avatar usuario={user} tamano="lg" />
        <div className="perfil-identidad">
          <h1 className="perfil-nombre">
            {user.nombre} {user.apellido}
          </h1>
          <p className="perfil-email">{user.email}</p>
        </div>
      </header>

      <section className="perfil-seccion" aria-labelledby="perfil-roles">
        <h2 id="perfil-roles" className="perfil-seccion-titulo">
          Roles
        </h2>
        <ul className="perfil-lista">
          <li className="perfil-fila">
            <Icono nombre="storefront" />
            <div className="perfil-fila-texto">
              <span className="perfil-fila-titulo">Organizador</span>
              <span className="perfil-fila-detalle">
                {organizador ? organizador.nombre_publico : "Todavía no publicás eventos."}
              </span>
            </div>
            {organizador && (
              <Badge variante={ESTADO_ORGANIZADOR[organizador.estado].variante}>
                {ESTADO_ORGANIZADOR[organizador.estado].texto}
              </Badge>
            )}
            {(!organizador || organizador.estado === "RECHAZADO") && (
              <Link to="/organizador/solicitud" className="perfil-fila-accion">
                Solicitar
              </Link>
            )}
          </li>
          {user.es_admin && (
            <li className="perfil-fila">
              <Icono nombre="admin_panel_settings" />
              <div className="perfil-fila-texto">
                <span className="perfil-fila-titulo">Administrador</span>
                <span className="perfil-fila-detalle">
                  Moderás eventos y solicitudes de organizador.
                </span>
              </div>
            </li>
          )}
        </ul>
      </section>

      <Button variant="outline" className="perfil-salir" onClick={logout}>
        <Icono nombre="logout" />
        Cerrar sesión
      </Button>
    </div>
  );
};

export default Perfil;
