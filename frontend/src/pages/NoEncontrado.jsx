import { Link } from "react-router-dom";
import Layout from "../components/layout/Layout";
import EmptyState from "../components/ui/EmptyState";
import Spinner from "../components/ui/Spinner";
import { useAuth } from "../features/auth/context/AuthContext";
import "./NoEncontrado.css";

const CLASES_BOTON = "btn-base btn-variant-default btn-size-default";

// Página 404 (ruta "*"). Con sesión se muestra dentro del layout, con la barra
// de navegación, para que el usuario siga desde ahí. Sin sesión se muestra
// sola, con un enlace al login, en vez de mandarlo primero a iniciar sesión
// para después decirle que la página no existe.
const NoEncontrado = () => {
  const { user, loading } = useAuth();

  if (loading) return <Spinner pantallaCompleta />;

  const contenido = (
    <EmptyState
      className="no-encontrado"
      icono="explore_off"
      titulo="No encontramos esta página"
      descripcion="Puede que el enlace esté mal escrito o que la página ya no exista."
    >
      {user ? (
        <Link to="/explorar" className={CLASES_BOTON}>
          Ir a Explorar
        </Link>
      ) : (
        <Link to="/ingresar" className={CLASES_BOTON}>
          Iniciar sesión
        </Link>
      )}
    </EmptyState>
  );

  if (!user) return <div className="no-encontrado-pantalla">{contenido}</div>;

  return (
    <Layout>
      <div className="pagina">{contenido}</div>
    </Layout>
  );
};

export default NoEncontrado;
