import Button from "../../../components/ui/Button";
import EmptyState from "../../../components/ui/EmptyState";
import Spinner from "../../../components/ui/Spinner";
import TarjetaEvento from "./TarjetaEvento";
import "./ListaEventos.css";

// Lista de resultados del descubrimiento (RF-03.2). Recibe el resultado de
// useBusquedaEventos() tal cual: el mapa (paso 5) va a usar el mismo.
// - hayFiltros / onLimpiarFiltros: para ofrecer "Limpiar filtros" cuando no
//   hay resultados.
const ListaEventos = ({ busqueda, hayFiltros, onLimpiarFiltros }) => {
  const { eventos, total, cargando, actualizando, error, hayMas, cargarMas, cargandoMas, reintentar } =
    busqueda;

  if (cargando) return <EsqueletoLista />;

  if (error && eventos.length === 0) {
    return (
      <EmptyState icono="cloud_off" titulo="No pudimos cargar los eventos" descripcion={error.message}>
        <Button variant="outline" onClick={reintentar}>
          Reintentar
        </Button>
      </EmptyState>
    );
  }

  if (eventos.length === 0) {
    return hayFiltros ? (
      <EmptyState
        icono="event_busy"
        titulo="No hay eventos con estos filtros"
        descripcion="Probá con otras fechas, otro horario o más categorías."
      >
        <Button variant="outline" onClick={onLimpiarFiltros}>
          Limpiar filtros
        </Button>
      </EmptyState>
    ) : (
      <EmptyState
        icono="event"
        titulo="Todavía no hay eventos"
        descripcion="Cuando se publiquen eventos, los vas a ver acá."
      />
    );
  }

  return (
    <section
      className={`lista-eventos ${actualizando ? "lista-eventos-actualizando" : ""}`.trim()}
      aria-label="Eventos"
      aria-busy={actualizando}
    >
      <p className="lista-eventos-total" aria-live="polite">
        {total === 1 ? "1 evento" : `${total} eventos`}
        {actualizando && <Spinner tamano="sm" etiqueta="Actualizando" />}
      </p>

      <ul className="lista-eventos-items">
        {eventos.map((evento) => (
          <li key={evento.id_evento}>
            <TarjetaEvento evento={evento} />
          </li>
        ))}
      </ul>

      {error && (
        <p className="lista-eventos-error" role="alert">
          {error.message}{" "}
          <button type="button" onClick={reintentar}>
            Reintentar
          </button>
        </p>
      )}

      {hayMas && (
        <div className="lista-eventos-mas">
          <Button variant="outline" onClick={cargarMas} disabled={cargandoMas} aria-busy={cargandoMas}>
            {cargandoMas && <Spinner tamano="sm" decorativo />}
            {cargandoMas ? "Cargando..." : `Cargar más (${total - eventos.length})`}
          </Button>
        </div>
      )}
    </section>
  );
};

// Siluetas de tarjetas mientras llega la primera página: la página no salta
// cuando aparecen los resultados.
const EsqueletoLista = () => (
  <div className="lista-eventos" role="status" aria-label="Cargando eventos">
    <span className="lista-eventos-total">
      <span className="esqueleto" style={{ width: "5rem" }} />
    </span>
    <ul className="lista-eventos-items" aria-hidden="true">
      {[70, 55, 80, 60].map((ancho, i) => (
        <li key={i} className="lista-eventos-esqueleto">
          <span className="esqueleto lista-eventos-esqueleto-fecha" />
          <span className="lista-eventos-esqueleto-cuerpo">
            <span className="esqueleto" style={{ width: `${ancho}%`, height: "1rem" }} />
            <span className="esqueleto" style={{ width: "45%" }} />
            <span className="esqueleto" style={{ width: "60%" }} />
          </span>
        </li>
      ))}
    </ul>
  </div>
);

export default ListaEventos;
