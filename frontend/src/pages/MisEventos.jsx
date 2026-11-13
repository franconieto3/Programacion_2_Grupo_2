import { useId } from "react";
import { Link } from "react-router-dom";
import Button from "../components/ui/Button";
import EmptyState from "../components/ui/EmptyState";
import Icono from "../components/ui/Icono";
import BotonCancelarEvento from "../features/eventos/components/BotonCancelarEvento";
import FilaMiEvento from "../features/eventos/components/FilaMiEvento";
import { useAuth } from "../features/auth/context/AuthContext";
import { useMisEventos } from "../features/eventos/hooks/useMisEventos";
import { permisosSobre } from "../features/eventos/permisos";
import "./MisEventos.css";

const CLASES_BOTON = "btn-base btn-variant-default btn-size-default";
const CLASES_ICONO = "btn-base btn-variant-ghost btn-size-icon";

// "Mis eventos" del organizador (RF-02.5): todos sus eventos con su estado,
// separados en próximos y finalizados. Solo para organizadores aprobados
// (OrganizadorRoute).
const MisEventos = () => {
  const { eventos, proximos, finalizados, isPending, error, refetch } = useMisEventos();

  let contenido;
  if (isPending) {
    contenido = <EsqueletoMisEventos />;
  } else if (error) {
    contenido = (
      <EmptyState icono="cloud_off" titulo="No pudimos cargar tus eventos" descripcion={error.message}>
        <Button variant="outline" onClick={() => refetch()}>
          Reintentar
        </Button>
      </EmptyState>
    );
  } else if (eventos.length === 0) {
    contenido = (
      <EmptyState
        icono="event_available"
        titulo="Todavía no publicaste eventos"
        descripcion="Cuando publiques uno, lo vas a ver acá con su estado."
      >
        <Link to="/eventos/nuevo" className={CLASES_BOTON}>
          Crear evento
        </Link>
      </EmptyState>
    );
  } else {
    contenido = (
      <>
        <Grupo
          titulo="Próximos"
          eventos={proximos}
          vacio="No tenés eventos por delante."
        />
        {finalizados.length > 0 && <Grupo titulo="Finalizados" eventos={finalizados} />}
      </>
    );
  }

  return (
    <div className="pagina">
      <header className="mis-eventos-encabezado">
        <h1 className="pagina-titulo mis-eventos-titulo">Mis eventos</h1>
        {eventos.length > 0 && (
          <Link to="/eventos/nuevo" className={`${CLASES_BOTON} mis-eventos-crear`}>
            <Icono nombre="add" />
            Crear evento
          </Link>
        )}
      </header>
      {contenido}
    </div>
  );
};

const Grupo = ({ titulo, eventos, vacio }) => {
  const id = useId();
  const { user } = useAuth();
  return (
    <section className="mis-eventos-grupo" aria-labelledby={id}>
      <h2 id={id} className="mis-eventos-grupo-titulo">
        {titulo}
        <span className="mis-eventos-grupo-cantidad">{eventos.length}</span>
      </h2>
      {eventos.length === 0 ? (
        <p className="mis-eventos-grupo-vacio">{vacio}</p>
      ) : (
        <ul className="mis-eventos-lista">
          {eventos.map((evento) => (
            <li key={evento.id_evento}>
              <FilaMiEvento evento={evento}>
                <Acciones evento={evento} permisos={permisosSobre(evento, user)} />
              </FilaMiEvento>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
};

// Editar y cancelar (RF-02.4), solo los que permite el estado del evento.
const Acciones = ({ evento, permisos }) => (
  <>
    {permisos.puedeEditar && (
      <Link
        to={`/eventos/${evento.id_evento}/editar`}
        className={CLASES_ICONO}
        aria-label={`Editar «${evento.titulo}»`}
        title="Editar"
      >
        <Icono nombre="edit" />
      </Link>
    )}
    {permisos.puedeCancelar && <BotonCancelarEvento evento={evento} compacto />}
  </>
);

const EsqueletoMisEventos = () => (
  <ul className="mis-eventos-lista" role="status" aria-label="Cargando tus eventos">
    {[65, 50, 75].map((ancho, i) => (
      <li key={i} className="mis-eventos-esqueleto" aria-hidden="true">
        <span className="esqueleto mis-eventos-esqueleto-fecha" />
        <span className="mis-eventos-esqueleto-cuerpo">
          <span className="esqueleto" style={{ width: "5rem" }} />
          <span className="esqueleto" style={{ width: `${ancho}%`, height: "1rem" }} />
          <span className="esqueleto" style={{ width: "45%" }} />
        </span>
      </li>
    ))}
  </ul>
);

export default MisEventos;
