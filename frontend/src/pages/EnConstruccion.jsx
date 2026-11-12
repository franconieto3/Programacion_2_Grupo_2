import Icono from "../components/ui/Icono";
import "./EnConstruccion.css";

// Página provisoria para las rutas de la barra de navegación que todavía no
// están hechas (ver docs/08-hoja-de-ruta-frontend.md). Se reemplaza por la
// página real en la etapa que corresponda.
const EnConstruccion = ({ titulo, icono, descripcion }) => (
  <div className="pagina">
    <h1 className="pagina-titulo">{titulo}</h1>
    <div className="en-construccion">
      <span className="en-construccion-icono">
        <Icono nombre={icono} />
      </span>
      <p className="en-construccion-titulo">Próximamente</p>
      <p className="en-construccion-texto">{descripcion}</p>
    </div>
  </div>
);

export default EnConstruccion;
