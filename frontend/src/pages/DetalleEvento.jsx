import { Link, useLocation, useNavigate, useParams } from "react-router-dom";
import MapaUbicacion from "../components/mapa/MapaUbicacion";
import Avatar from "../components/ui/Avatar";
import Badge from "../components/ui/Badge";
import Button from "../components/ui/Button";
import EmptyState from "../components/ui/EmptyState";
import Icono from "../components/ui/Icono";
import BadgeEquipo from "../features/eventos/components/BadgeEquipo";
import { cuandoDetalle, precio, yaTermino } from "../features/eventos/formato";
import { useEvento } from "../features/eventos/hooks/useEvento";
import "./DetalleEvento.css";

const CLASES_BOTON = "btn-base btn-variant-outline btn-size-default";

// Ficha de detalle de un evento (RF-03.10, CU-01 paso 5): datos, lugar con un
// mapa chico, precio, categorías y quién lo publica.
const DetalleEvento = () => {
  const { idEvento } = useParams();
  const { data: evento, isPending, error, noEncontrado, refetch } = useEvento(idEvento);

  let contenido;
  if (noEncontrado) {
    contenido = (
      <EmptyState
        icono="event_busy"
        titulo="No encontramos este evento"
        descripcion="Puede que el enlace esté mal escrito o que el evento ya no esté disponible."
      >
        <Link to="/explorar" className={CLASES_BOTON}>
          Ir a Explorar
        </Link>
      </EmptyState>
    );
  } else if (error) {
    contenido = (
      <EmptyState icono="cloud_off" titulo="No pudimos cargar el evento" descripcion={error.message}>
        <Button variant="outline" onClick={() => refetch()}>
          Reintentar
        </Button>
      </EmptyState>
    );
  } else if (isPending) {
    contenido = <EsqueletoDetalle />;
  } else {
    contenido = <Ficha evento={evento} />;
  }

  return (
    <div className="pagina">
      <BotonVolver />
      {contenido}
    </div>
  );
};

const Ficha = ({ evento }) => {
  const { lugar, organizador } = evento;
  const cuando = cuandoDetalle(evento);
  const textoPrecio = precio(evento.precio);
  const terminado = yaTermino(evento);
  const finalizado = terminado && evento.estado !== "CANCELADO";
  const delEquipo = evento.origen === "SEED_EQUIPO";
  const urlMapa = `https://www.openstreetmap.org/?mlat=${lugar.latitud}&mlon=${lugar.longitud}#map=17/${lugar.latitud}/${lugar.longitud}`;

  return (
    <article className="detalle-evento">
      <header className="detalle-evento-encabezado">
        {(delEquipo || evento.estado === "BORRADOR" || finalizado) && (
          <div className="detalle-evento-estados">
            <BadgeEquipo evento={evento} />
            {evento.estado === "BORRADOR" && (
              <Badge variante="advertencia" icono="edit_note">
                Borrador
              </Badge>
            )}
            {finalizado && <Badge icono="history">Finalizado</Badge>}
          </div>
        )}
        <h1 className="detalle-evento-titulo">{evento.titulo}</h1>
        {evento.categorias.length > 0 && (
          <ul className="detalle-evento-categorias" aria-label="Categorías">
            {evento.categorias.map((categoria) => (
              <li key={categoria.slug}>
                <Badge>{categoria.nombre}</Badge>
              </li>
            ))}
          </ul>
        )}
      </header>

      {evento.estado === "CANCELADO" && (
        <p className="detalle-evento-aviso" role="status">
          <Icono nombre="event_busy" />
          Este evento fue cancelado.
        </p>
      )}

      <ul className="detalle-evento-datos">
        <li className="detalle-evento-dato">
          <span className="detalle-evento-dato-icono">
            <Icono nombre="calendar_today" />
          </span>
          <span className="detalle-evento-dato-texto">
            <span className="detalle-evento-dato-principal">{cuando.principal}</span>
            <span>{cuando.secundario}</span>
          </span>
        </li>
        <li className="detalle-evento-dato">
          <span className="detalle-evento-dato-icono">
            <Icono nombre="location_on" />
          </span>
          <span className="detalle-evento-dato-texto">
            <span className="detalle-evento-dato-principal">
              {lugar.nombre ?? lugar.direccion ?? "Ubicación en el mapa"}
            </span>
            {lugar.nombre && lugar.direccion && <span>{lugar.direccion}</span>}
            <a className="detalle-evento-enlace" href={urlMapa} target="_blank" rel="noreferrer">
              Abrir en OpenStreetMap
              <Icono nombre="open_in_new" />
              <span className="sr-only">(se abre en otra pestaña)</span>
            </a>
          </span>
        </li>
        {textoPrecio && (
          <li className="detalle-evento-dato">
            <span className="detalle-evento-dato-icono">
              <Icono nombre="confirmation_number" />
            </span>
            <span className="detalle-evento-dato-texto">
              <span className="detalle-evento-dato-principal">{textoPrecio}</span>
              <span>Entrada</span>
            </span>
          </li>
        )}
      </ul>

      <MapaUbicacion
        lat={lugar.latitud}
        lng={lugar.longitud}
        titulo={lugar.nombre ?? evento.titulo}
        className="detalle-evento-mapa"
      />

      <section className="detalle-evento-seccion" aria-labelledby="detalle-descripcion">
        <h2 id="detalle-descripcion" className="detalle-evento-seccion-titulo">
          Sobre el evento
        </h2>
        <p className="detalle-evento-descripcion">{evento.descripcion}</p>
      </section>

      <section className="detalle-evento-seccion" aria-labelledby="detalle-organizador">
        <h2 id="detalle-organizador" className="detalle-evento-seccion-titulo">
          Publicado por
        </h2>
        <div className="detalle-evento-organizador">
          {organizador.id_organizador ? (
            <Avatar usuario={inicialesDe(organizador.nombre_publico)} />
          ) : (
            // Eventos de seed (RF-05.2): el "organizador" es el equipo, con el logo.
            <span className="avatar avatar-md detalle-evento-equipo" aria-hidden="true">
              <Icono nombre="location_on" relleno />
            </span>
          )}
          <span className="detalle-evento-organizador-texto">
            <span className="detalle-evento-dato-principal">{organizador.nombre_publico}</span>
            <span>{organizador.descripcion}</span>
          </span>
        </div>
      </section>
    </article>
  );
};

// Avatar espera { nombre, apellido }: con la primera y la última palabra del
// nombre público, "Bar Los Pinos" muestra "BP".
function inicialesDe(nombrePublico) {
  const palabras = nombrePublico.trim().split(/\s+/);
  return { nombre: palabras[0], apellido: palabras.length > 1 ? palabras.at(-1) : "" };
}

// Vuelve a la página anterior (la lista, con sus filtros). Si se entró
// directo a la ficha (un enlace compartido), no hay página anterior en la
// app: va a Explorar.
const BotonVolver = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const hayAnterior = location.key !== "default";

  return (
    <Button
      variant="ghost"
      size="sm"
      className="detalle-evento-volver"
      onClick={() => (hayAnterior ? navigate(-1) : navigate("/explorar"))}
    >
      <Icono nombre="arrow_back" />
      {hayAnterior ? "Volver" : "Explorar"}
    </Button>
  );
};

const EsqueletoDetalle = () => (
  <div className="detalle-evento" role="status" aria-label="Cargando el evento">
    <div aria-hidden="true">
      <span className="esqueleto" style={{ width: "70%", height: "2rem" }} />
      <span className="esqueleto" style={{ width: "9rem", height: "1.25rem", marginTop: "1rem" }} />
      <div className="detalle-evento-datos" style={{ marginTop: "2rem" }}>
        {[60, 75].map((ancho) => (
          <div key={ancho} className="detalle-evento-dato">
            <span className="esqueleto detalle-evento-dato-icono" />
            <span className="detalle-evento-dato-texto" style={{ flex: 1, gap: "0.5rem" }}>
              <span className="esqueleto" style={{ width: `${ancho}%`, height: "1rem" }} />
              <span className="esqueleto" style={{ width: "40%" }} />
            </span>
          </div>
        ))}
      </div>
    </div>
  </div>
);

export default DetalleEvento;
