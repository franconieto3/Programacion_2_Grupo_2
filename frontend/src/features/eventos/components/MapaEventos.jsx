import { useEffect, useMemo, useRef } from "react";
import { Link } from "react-router-dom";
import { Marker, Popup, useMap } from "react-leaflet";
import Mapa from "../../../components/mapa/Mapa";
import { iconoMarcador } from "../../../components/mapa/marcador";
import Spinner from "../../../components/ui/Spinner";
import { cuando } from "../formato";
import "./MapaEventos.css";

// Mapa del descubrimiento (RF-03.1, RF-03.3): un marcador por lugar con un
// popup que lleva al detalle. No busca por su cuenta: avisa cuándo cambia lo
// que se ve y la página le pasa los eventos de useBusquedaEventos(), los
// mismos que muestra la lista (RF-03.2).
//
// - eventos: los de useBusquedaEventos().
// - centro: { lat, lng, zoom } inicial.
// - onCambioViewport(viewport, { centro, zoom }): al montarse y cada vez que
//   el usuario termina de mover o hacer zoom (con `espera` ms de debounce, 400
//   por defecto). viewport es { lat_min, lat_max, lng_min, lng_max }:
//   pasárselo tal cual a useBusquedaEventos, que lo normaliza. centro
//   ({ lat, lng }) y zoom sirven para guardar la posición (p. ej. en la URL).
// - onInteraccion(): cuando el usuario empieza a arrastrar o hacer zoom.
// - actualizando: muestra "Buscando..." sobre el mapa.
// - total: cuántos eventos cumplen la búsqueda; si son más que los marcados,
//   lo avisa ("50 de 120 en el mapa").
// - ref: la instancia de Leaflet, para moverlo desde afuera (fitBounds del
//   buscador de lugares, paso 6).
const MapaEventos = ({
  eventos,
  centro,
  onCambioViewport,
  onInteraccion,
  espera = 400,
  actualizando = false,
  total = 0,
  className = "",
  ref,
}) => {
  const grupos = useMemo(() => agruparPorLugar(eventos), [eventos]);

  return (
    <div className={`mapa-eventos ${className}`.trim()}>
      <Mapa centro={centro} zoom={centro.zoom} ref={ref} className="mapa-eventos-mapa">
        <EscuchaViewport onCambio={onCambioViewport} onInteraccion={onInteraccion} espera={espera} />
        {grupos.map((grupo) => (
          <Marker
            key={grupo.clave}
            position={[grupo.lat, grupo.lng]}
            icon={iconoMarcador(grupo.eventos.length)}
            title={tituloMarcador(grupo)}
          >
            <Popup>
              <ContenidoPopup grupo={grupo} />
            </Popup>
          </Marker>
        ))}
      </Mapa>
      {actualizando ? (
        <span className="mapa-eventos-estado">
          <Spinner tamano="sm" decorativo />
          Buscando...
        </span>
      ) : (
        total > eventos.length && (
          <span className="mapa-eventos-estado">
            {eventos.length} de {total} en el mapa
          </span>
        )
      )}
    </div>
  );
};

// Avisa el viewport al montarse (para la primera búsqueda) y después de cada
// movimiento, esperando a que el usuario termine (debounce): arrastrar el
// mapa dispara muchos "moveend" seguidos.
const EscuchaViewport = ({ onCambio, onInteraccion, espera }) => {
  const map = useMap();
  const alCambiar = useRef(onCambio);
  const alInteractuar = useRef(onInteraccion);

  useEffect(() => {
    alCambiar.current = onCambio;
    alInteractuar.current = onInteraccion;
  }, [onCambio, onInteraccion]);

  // Arrastrar o hacer zoom (con la rueda, los botones o los dedos). Se
  // escucha recién después de montarse: la posición inicial no cuenta.
  useEffect(() => {
    const interactuar = () => alInteractuar.current?.();
    map.on("dragstart zoomstart", interactuar);
    return () => map.off("dragstart zoomstart", interactuar);
  }, [map]);

  useEffect(() => {
    let temporizador;
    const avisar = () => {
      const { lat, lng } = map.getCenter().wrap();
      alCambiar.current?.(viewportDe(map), { centro: { lat, lng }, zoom: map.getZoom() });
    };
    const alMover = () => {
      clearTimeout(temporizador);
      temporizador = setTimeout(avisar, espera);
    };
    avisar();
    map.on("moveend", alMover);
    return () => {
      clearTimeout(temporizador);
      map.off("moveend", alMover);
    };
  }, [map, espera]);

  return null;
};

const ContenidoPopup = ({ grupo }) => {
  if (grupo.eventos.length === 1) {
    const [evento] = grupo.eventos;
    return (
      <div className="popup-evento">
        <Link to={`/eventos/${evento.id_evento}`} className="popup-evento-titulo">
          {evento.titulo}
        </Link>
        <span>{cuando(evento)}</span>
        {grupo.nombreLugar && <span className="popup-evento-lugar">{grupo.nombreLugar}</span>}
      </div>
    );
  }

  return (
    <div className="popup-evento">
      <span className="popup-evento-encabezado">
        {grupo.nombreLugar ?? "En este lugar"} · {grupo.eventos.length} eventos
      </span>
      <ul className="popup-evento-lista">
        {grupo.eventos.map((evento) => (
          <li key={evento.id_evento}>
            <Link to={`/eventos/${evento.id_evento}`} className="popup-evento-titulo">
              {evento.titulo}
            </Link>
            <span>{cuando(evento)}</span>
          </li>
        ))}
      </ul>
    </div>
  );
};

// Bordes de lo que se ve, con los nombres que espera buscarEventos().
function viewportDe(map) {
  const limites = map.getBounds();
  return {
    lat_min: limites.getSouth(),
    lat_max: limites.getNorth(),
    lng_min: limites.getWest(),
    lng_max: limites.getEast(),
  };
}

// Junta los eventos con las mismas coordenadas (p. ej. varias fechas en el
// mismo bar), conservando el orden de la búsqueda (los más próximos primero).
function agruparPorLugar(eventos) {
  const grupos = new Map();
  for (const evento of eventos) {
    const { latitud, longitud, nombre } = evento.lugar;
    const clave = `${latitud},${longitud}`;
    if (!grupos.has(clave)) {
      grupos.set(clave, { clave, lat: latitud, lng: longitud, nombreLugar: nombre, eventos: [] });
    }
    grupos.get(clave).eventos.push(evento);
  }
  return [...grupos.values()];
}

function tituloMarcador(grupo) {
  if (grupo.eventos.length === 1) return grupo.eventos[0].titulo;
  return `${grupo.nombreLugar ?? "Lugar"}: ${grupo.eventos.length} eventos`;
}

export default MapaEventos;
