import EmptyState from "../components/ui/EmptyState";

// Página provisoria para las rutas de la barra de navegación que todavía no
// están hechas (ver docs/08-hoja-de-ruta-frontend.md). Se reemplaza por la
// página real en la etapa que corresponda.
const EnConstruccion = ({ titulo, icono, descripcion }) => (
  <div className="pagina">
    <h1 className="pagina-titulo">{titulo}</h1>
    <EmptyState icono={icono} titulo="Próximamente" descripcion={descripcion} />
  </div>
);

export default EnConstruccion;
