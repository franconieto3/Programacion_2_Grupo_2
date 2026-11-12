import { useEffect } from "react";
import { MapContainer, TileLayer, useMap } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import "./Mapa.css";

// Mapa base de la app (Leaflet + tiles de OpenStreetMap). Lo usan el
// descubrimiento (MapaEventos), la ficha de un evento (MapaUbicacion) y, en la
// etapa 3, el selector de ubicación del formulario de eventos.
//
// - centro: { lat, lng } y zoom: posición inicial. Como en react-leaflet, no
//   se pueden cambiar después de montarlo: para mover el mapa usar la
//   instancia (ref o useMap()) con setView / fitBounds.
// - El resto de las props van a MapContainer (scrollWheelZoom, dragging, ref...).
// - El tamaño lo define quien lo usa con `className` (necesita una altura).
//
// La atribución a OpenStreetMap es obligatoria por su licencia (ODbL) y su
// política de uso de tiles: no sacarla.
const ATRIBUCION =
  '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>';

const Mapa = ({ centro, zoom, className = "", children, ...opciones }) => (
  <MapContainer
    center={[centro.lat, centro.lng]}
    zoom={zoom}
    minZoom={3}
    worldCopyJump
    className={`mapa ${className}`.trim()}
    {...opciones}
  >
    <TileLayer url="https://tile.openstreetmap.org/{z}/{x}/{y}.png" attribution={ATRIBUCION} maxZoom={19} />
    <AjustarTamano />
    {children}
  </MapContainer>
);

// Leaflet calcula su tamaño al montarse; si después cambia el contenedor
// (se abre un panel, se pasa de lista a mapa en el celular...) quedan zonas
// grises. Se le avisa cada vez que cambia.
const AjustarTamano = () => {
  const map = useMap();
  useEffect(() => {
    const observador = new ResizeObserver(() => map.invalidateSize());
    observador.observe(map.getContainer());
    return () => observador.disconnect();
  }, [map]);
  return null;
};

export default Mapa;
