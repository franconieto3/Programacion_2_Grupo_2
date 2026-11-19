import Logo from "./Logo";
import { NOMBRE_APP } from "./marca";
import "./Pie.css";

// Fuera del render: el año no cambia mientras la app está abierta.
const ANIO = new Date().getFullYear();

// Footer de la app: marca + leyenda. Se usa en el layout con sesión y en las
// pantallas de autenticación.
const Pie = ({ className = "" }) => (
  <footer className={`pie ${className}`.trim()}>
    <Logo size={22} />
    <p className="pie-texto">
      © {ANIO} {NOMBRE_APP} · Descubrí eventos cerca tuyo
    </p>
  </footer>
);

export default Pie;
