import L from "leaflet";
import { Marker } from "react-leaflet";
import Mapa from "./Mapa";
import { iconoMarcador } from "./marcador";

// Mapa chico con un solo punto, como el lugar en la ficha de un evento.
// Para no "atrapar" el scroll de la página: la rueda del mouse no hace zoom
// y en pantallas táctiles no se arrastra con un dedo (quedan los botones +/−).
const MapaUbicacion = ({ lat, lng, titulo, zoom = 16, className = "" }) => (
  <Mapa
    centro={{ lat, lng }}
    zoom={zoom}
    scrollWheelZoom={false}
    dragging={!L.Browser.mobile}
    className={`mapa-ubicacion ${className}`.trim()}
  >
    <Marker position={[lat, lng]} icon={iconoMarcador()} title={titulo} interactive={false} />
  </Mapa>
);

export default MapaUbicacion;
