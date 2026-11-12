import "./Spinner.css";

// Indicador de carga. Toma el color del texto que lo rodea (currentColor).
// - tamano: "sm" (16px, dentro de botones), "md" (24px) o "lg" (36px).
// - etiqueta: lo que anuncia el lector de pantalla.
// - decorativo: sin anuncio propio, para cuando el contenedor ya lo comunica
//   (p. ej. un botón con aria-busy).
// - pantallaCompleta: centrado en toda la pantalla, y aparece recién a los
//   300 ms para que las cargas rápidas no hagan un parpadeo.
const Spinner = ({
  tamano,
  etiqueta = "Cargando",
  decorativo = false,
  pantallaCompleta = false,
  className = "",
}) => {
  const spinner = (
    <span
      className={`spinner spinner-${tamano ?? (pantallaCompleta ? "lg" : "md")} ${className}`.trim()}
      role={decorativo ? undefined : "status"}
      aria-hidden={decorativo || undefined}
    >
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <circle className="spinner-pista" cx="12" cy="12" r="10" />
        <path className="spinner-arco" d="M22 12a10 10 0 0 0-10-10" />
      </svg>
      {!decorativo && <span className="sr-only">{etiqueta}</span>}
    </span>
  );

  return pantallaCompleta ? <div className="spinner-pantalla">{spinner}</div> : spinner;
};

export default Spinner;
