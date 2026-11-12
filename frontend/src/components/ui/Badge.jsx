import Icono from "./Icono";
import "./Badge.css";

// Etiqueta chica para estados y categorías.
// variante: "neutral" (por defecto), "exito", "advertencia", "error" o "info".
// Ejemplos: estado de un evento (BadgeEstado), "Equipo de la plataforma",
// categorías en las tarjetas.
const Badge = ({ variante = "neutral", icono, children, className = "" }) => (
  <span className={`badge badge-${variante} ${className}`.trim()}>
    {icono && <Icono nombre={icono} />}
    {children}
  </span>
);

export default Badge;
