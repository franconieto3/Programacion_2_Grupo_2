import Icono from "./Icono";
import "./EmptyState.css";

// Lo que se muestra cuando no hay nada para listar (sin eventos, sin
// resultados para los filtros...). `children` es la acción opcional, por
// ejemplo un enlace a "Crear evento".
const EmptyState = ({ icono, titulo, descripcion, children, className = "" }) => (
  <div className={`empty-state ${className}`.trim()}>
    {icono && (
      <span className="empty-state-icono">
        <Icono nombre={icono} />
      </span>
    )}
    <p className="empty-state-titulo">{titulo}</p>
    {descripcion && <p className="empty-state-texto">{descripcion}</p>}
    {children && <div className="empty-state-accion">{children}</div>}
  </div>
);

export default EmptyState;
