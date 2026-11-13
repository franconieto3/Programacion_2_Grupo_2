import { aValorFechaHora } from './formato'

// Para la edición (RF-02.4): de los datos completos de FormularioEvento, deja
// solo lo que cambió respecto del evento como lo devolvió la API, que es lo
// que espera el PATCH. Devuelve {} si no cambió nada.
// - Las fechas se comparan al minuto (lo que muestra el input).
// - El precio, como número ("1500.50" y "1500.5" son el mismo).
// - El lugar va completo si cambió algo (el backend lo reemplaza entero).
// - Las categorías, sin importar el orden.
export function cambiosEntre(evento, datos) {
  const cambios = {}
  if (datos.titulo !== evento.titulo) cambios.titulo = datos.titulo
  if (datos.descripcion !== evento.descripcion) cambios.descripcion = datos.descripcion
  if (!mismaFecha(datos.fecha_inicio, evento.fecha_inicio)) cambios.fecha_inicio = datos.fecha_inicio
  if (!mismaFecha(datos.fecha_fin, evento.fecha_fin)) cambios.fecha_fin = datos.fecha_fin
  if (numero(datos.precio) !== numero(evento.precio)) cambios.precio = datos.precio
  if (!mismoLugar(datos.lugar, evento.lugar)) cambios.lugar = datos.lugar

  const slugs = evento.categorias.map((c) => c.slug)
  if (!mismosElementos(datos.categorias, slugs)) cambios.categorias = datos.categorias
  return cambios
}

function mismaFecha(a, b) {
  if (!a || !b) return !a && !b
  return aValorFechaHora(a) === aValorFechaHora(b)
}

function numero(valor) {
  return valor === null || valor === undefined || valor === '' ? null : Number(valor)
}

function mismoLugar(a, b) {
  return (
    a.latitud === b.latitud &&
    a.longitud === b.longitud &&
    (a.nombre ?? null) === (b.nombre ?? null) &&
    (a.direccion ?? null) === (b.direccion ?? null)
  )
}

function mismosElementos(a, b) {
  return a.length === b.length && a.every((x) => b.includes(x))
}
