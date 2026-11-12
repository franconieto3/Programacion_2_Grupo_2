import { useEffect, useId, useRef, useState } from "react";
import { useAuth } from "../../features/auth/context/AuthContext";
import Avatar from "../ui/Avatar";
import Icono from "../ui/Icono";

// Botón de la cuenta al pie de la barra lateral (como en X): muestra quién
// está logueado y abre un menú con "Cerrar sesión". En el celular no se
// muestra; ahí se cierra sesión desde la página de perfil.
const MenuCuenta = () => {
  const { user, logout } = useAuth();
  const [abierto, setAbierto] = useState(false);
  const contenedor = useRef(null);
  const idMenu = useId();

  // Se cierra con Escape o con un clic afuera.
  useEffect(() => {
    if (!abierto) return;
    const alClic = (evento) => {
      if (!contenedor.current?.contains(evento.target)) setAbierto(false);
    };
    const alTecla = (evento) => {
      if (evento.key === "Escape") setAbierto(false);
    };
    document.addEventListener("mousedown", alClic);
    document.addEventListener("keydown", alTecla);
    return () => {
      document.removeEventListener("mousedown", alClic);
      document.removeEventListener("keydown", alTecla);
    };
  }, [abierto]);

  return (
    <div className="cuenta" ref={contenedor}>
      {abierto && (
        <div className="cuenta-menu" id={idMenu} role="menu">
          <button
            type="button"
            role="menuitem"
            className="cuenta-menu-item"
            onClick={logout}
          >
            <Icono nombre="logout" />
            Cerrar sesión
          </button>
        </div>
      )}
      <button
        type="button"
        className="cuenta-boton"
        aria-haspopup="menu"
        aria-expanded={abierto}
        aria-controls={abierto ? idMenu : undefined}
        aria-label={`Cuenta de ${user.nombre ?? user.email}`}
        title={user.email}
        onClick={() => setAbierto((valor) => !valor)}
      >
        <Avatar usuario={user} />
        <span className="cuenta-datos">
          <span className="cuenta-nombre">
            {user.nombre} {user.apellido}
          </span>
          <span className="cuenta-email">{user.email}</span>
        </span>
        <Icono nombre="more_horiz" className="cuenta-mas" />
      </button>
    </div>
  );
};

export default MenuCuenta;
