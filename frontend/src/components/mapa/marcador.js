import L from 'leaflet'

// Ícono de los marcadores: un pin dibujado con CSS (Mapa.css) en vez de las
// imágenes de Leaflet, que con Vite no se encuentran y no cambian con el modo
// oscuro. Con `cantidad` > 1 muestra el número (varios eventos en el mismo
// lugar). Se reutiliza el mismo objeto para cada cantidad.
const cache = new Map()

export function iconoMarcador(cantidad = 1) {
  if (!cache.has(cantidad)) {
    const contenido =
      cantidad > 1
        ? `<span class="marcador-cantidad">${cantidad > 99 ? '99+' : cantidad}</span>`
        : '<span class="marcador-punto"></span>'
    cache.set(
      cantidad,
      L.divIcon({
        className: 'marcador',
        html: `<span class="marcador-pin">${contenido}</span>`,
        iconSize: [32, 40],
        iconAnchor: [16, 38], // la punta del pin
        popupAnchor: [0, -34],
      }),
    )
  }
  return cache.get(cantidad)
}
