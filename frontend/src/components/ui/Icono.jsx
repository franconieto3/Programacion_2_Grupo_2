import "./Icono.css";

// Ícono de Material Symbols (https://fonts.google.com/icons): `nombre` es el
// nombre del ícono en esa página. `relleno` lo muestra lleno en vez de contorno,
// como el ítem activo de la barra de navegación.
// Es decorativo: el texto accesible lo pone quien lo usa (label, aria-label...).
const Icono = ({ nombre, relleno = false, className = "", ...props }) => (
  <span
    className={`material-symbols-outlined icono ${relleno ? "icono-relleno" : ""} ${className}`.trim()}
    aria-hidden="true"
    {...props}
  >
    {nombre}
  </span>
);

export default Icono;
