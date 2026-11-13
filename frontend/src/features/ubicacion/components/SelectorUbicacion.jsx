import { useId, useRef, useState } from "react";
import { Marker, useMapEvents } from "react-leaflet";
import Mapa from "../../../components/mapa/Mapa";
import { iconoMarcador } from "../../../components/mapa/marcador";
import Button from "../../../components/ui/Button";
import Icono from "../../../components/ui/Icono";
import { useUbicacionInicial } from "../hooks/useUbicacionInicial";
import BuscadorLugar from "./BuscadorLugar";
import "./SelectorUbicacion.css";

// Elegir dónde es un evento marcando un punto en el mapa (RF-02.2). Es
// controlado: el formulario guarda el punto y arma el `lugar` que manda a la
// API ({ latitud, longitud, nombre?, direccion? }; las coordenadas mandan).
//
//   <SelectorUbicacion valor={punto} onCambiar={(punto, { lugar }) => ...} error={errores.lugar} />
//
// - valor: { latitud, longitud } o null si todavía no se marcó.
// - onCambiar(punto, { lugar }): `lugar` es el resultado del buscador cuando
//   el punto salió de ahí (con su `nombre` completo, p. ej. para sugerir la
//   dirección), y null si se marcó en el mapa.
// - error: mensaje bajo el mapa (p. ej. "Marcá dónde es el evento").
//
// Formas de marcar: clic en el mapa, arrastrar el pin, elegir una dirección
// en el buscador o, con teclado, mover el mapa con las flechas y usar "Marcar
// el centro del mapa". Si el valor inicial existe (edición), el mapa abre
// ahí; si no, en la ubicación del usuario o la por defecto.
const ZOOM_PUNTO = 16;
// Un resultado del buscador cuyo recuadro mide menos que esto (en grados,
// unos 500 m) es un punto (una dirección, un local): se marca directo. Uno
// más grande (un barrio, una ciudad) solo acerca el mapa.
const TAMANO_PUNTO = 0.005;

const SelectorUbicacion = ({ valor, onCambiar, error, etiqueta = "Ubicación", className = "" }) => {
  const id = useId();
  const idAyuda = `${id}-ayuda`;
  const idError = `${id}-error`;
  const mapaRef = useRef(null);
  // Nombre de la zona elegida en el buscador que no se marcó sola.
  const [zonaBuscada, setZonaBuscada] = useState(null);

  // Dónde se monta el mapa: se fija una sola vez (como en Explorar).
  const inicial = useUbicacionInicial({ activo: !valor });
  const [centro, setCentro] = useState(() =>
    valor ? { lat: valor.latitud, lng: valor.longitud, zoom: ZOOM_PUNTO } : null,
  );
  if (!centro && inicial.ubicacion) setCentro(inicial.ubicacion);

  const marcar = (latlng, lugar = null) => {
    // Con worldCopyJump, Leaflet puede dar longitudes fuera de -180..180 y el
    // backend las rechaza. 6 decimales son unos 10 cm.
    const { lat, lng } = latlng.wrap ? latlng.wrap() : latlng;
    setZonaBuscada(null);
    onCambiar({ latitud: redondear(lat), longitud: redondear(lng) }, { lugar });
  };

  const alElegirLugar = (lugar) => {
    const mapa = mapaRef.current;
    const esPunto =
      lugar.lat_max - lugar.lat_min < TAMANO_PUNTO && lugar.lng_max - lugar.lng_min < TAMANO_PUNTO;
    if (esPunto) {
      mapa?.setView([lugar.lat, lugar.lng], Math.max(mapa.getZoom(), ZOOM_PUNTO));
      marcar({ lat: lugar.lat, lng: lugar.lng }, lugar);
    } else {
      mapa?.fitBounds(
        [
          [lugar.lat_min, lugar.lng_min],
          [lugar.lat_max, lugar.lng_max],
        ],
        { maxZoom: ZOOM_PUNTO },
      );
      setZonaBuscada(lugar.nombre.split(", ")[0]);
    }
  };

  return (
    <fieldset
      className={`selector-ubicacion ${className}`.trim()}
      aria-describedby={[idAyuda, error && idError].filter(Boolean).join(" ")}
    >
      <legend className="form-field-label selector-ubicacion-etiqueta">{etiqueta}</legend>

      <BuscadorLugar onSeleccionar={alElegirLugar} />

      <div
        className={`selector-ubicacion-mapa ${error ? "selector-ubicacion-mapa-invalido" : ""}`.trim()}
      >
        {centro ? (
          <>
            <Mapa
              ref={mapaRef}
              centro={centro}
              zoom={centro.zoom}
              className="selector-ubicacion-leaflet"
            >
              <AlHacerClic onClic={(latlng) => marcar(latlng)} />
              {valor && (
                <Marker
                  position={[valor.latitud, valor.longitud]}
                  icon={iconoMarcador()}
                  draggable
                  title="Lugar del evento (se puede arrastrar)"
                  eventHandlers={{ dragend: (evento) => marcar(evento.target.getLatLng()) }}
                />
              )}
            </Mapa>
            {/* Mira para "Marcar el centro del mapa": se ve con el foco en el mapa. */}
            <span className="selector-ubicacion-mira" aria-hidden="true">
              <Icono nombre="add" />
            </span>
          </>
        ) : (
          <div className="selector-ubicacion-esqueleto esqueleto" role="status" aria-label="Cargando el mapa" />
        )}
      </div>

      <div className="selector-ubicacion-pie">
        <p id={idAyuda} className="selector-ubicacion-ayuda" aria-live="polite">
          {ayuda(valor, zonaBuscada)}
        </p>
        <Button
          type="button"
          variant="outline"
          size="sm"
          disabled={!centro}
          onClick={() => mapaRef.current && marcar(mapaRef.current.getCenter())}
        >
          <Icono nombre="my_location" />
          Marcar el centro del mapa
        </Button>
      </div>

      {error && (
        <p id={idError} className="form-field-error">
          {error}
        </p>
      )}
    </fieldset>
  );
};

// Clic (o toque) en el mapa. Un arrastre no dispara "click" en Leaflet.
const AlHacerClic = ({ onClic }) => {
  useMapEvents({ click: (evento) => onClic(evento.latlng) });
  return null;
};

function ayuda(valor, zonaBuscada) {
  if (valor) {
    return `Marcado en ${valor.latitud.toFixed(5)}, ${valor.longitud.toFixed(5)}. Arrastrá el pin o hacé clic en otro punto para moverlo.`;
  }
  if (zonaBuscada) return `Te llevamos a ${zonaBuscada}. Ahora marcá el lugar exacto en el mapa.`;
  return "Buscá la dirección o hacé clic en el mapa para marcar dónde es el evento.";
}

function redondear(numero) {
  return Math.round(numero * 1e6) / 1e6;
}

export default SelectorUbicacion;
