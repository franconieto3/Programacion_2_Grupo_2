// Cómo se muestran fechas y precios de los eventos.
//
// Las fechas se muestran siempre en la zona horaria de la plataforma, la misma
// que usa el backend para los filtros (Settings.zona_horaria): si el filtro
// "desde el 14/11" incluye un evento, la tarjeta tiene que decir 14/11 aunque
// el navegador esté en otra zona.
export const ZONA_HORARIA = 'America/Argentina/Buenos_Aires'

const LOCALE = 'es-AR'

const formatoDia = new Intl.DateTimeFormat(LOCALE, {
  timeZone: ZONA_HORARIA,
  weekday: 'short',
  day: 'numeric',
  month: 'short',
})
const formatoHora = new Intl.DateTimeFormat(LOCALE, {
  timeZone: ZONA_HORARIA,
  hour: '2-digit',
  minute: '2-digit',
  hourCycle: 'h23',
})
// 'en-CA' da 'YYYY-MM-DD': sirve para comparar días y para los <input type="date">.
const formatoClaveDia = new Intl.DateTimeFormat('en-CA', {
  timeZone: ZONA_HORARIA,
  year: 'numeric',
  month: '2-digit',
  day: '2-digit',
})
const formatoPrecio = new Intl.NumberFormat(LOCALE, {
  style: 'currency',
  currency: 'ARS',
  minimumFractionDigits: 0,
  maximumFractionDigits: 2,
})

const MS_POR_DIA = 24 * 60 * 60 * 1000

// El backend guarda las fechas en UTC y con PostgreSQL las manda con zona
// ('2026-11-14T01:30:00Z'), pero con SQLite llegan sin ella y JavaScript las
// tomaría como hora local del navegador. Sin zona, se interpretan como UTC.
const TIENE_ZONA = /(Z|[+-]\d{2}:?\d{2})$/

export function aFecha(valor) {
  if (typeof valor === 'string' && valor.includes('T') && !TIENE_ZONA.test(valor)) {
    return new Date(`${valor}Z`)
  }
  return new Date(valor)
}

// Día en la zona de la plataforma, 'YYYY-MM-DD'.
export function claveDia(fecha) {
  return formatoClaveDia.format(aFecha(fecha))
}

function partes(fecha) {
  const resultado = {}
  for (const { type, value } of formatoDia.formatToParts(aFecha(fecha))) {
    resultado[type] = value.replace('.', '')
  }
  return resultado
}

const capitalizar = (texto) => texto.charAt(0).toUpperCase() + texto.slice(1)

// { mes: 'NOV', dia: '14' }: el bloque de fecha de la tarjeta.
export function bloqueFecha(fecha) {
  const { month, day } = partes(fecha)
  return { mes: month.toUpperCase(), dia: day }
}

// 'Hoy', 'Mañana' o 'Sáb 14 nov'.
export function diaRelativo(fecha, ahora = new Date()) {
  const dia = claveDia(fecha)
  if (dia === claveDia(ahora)) return 'Hoy'
  if (dia === claveDia(ahora.getTime() + MS_POR_DIA)) return 'Mañana'
  const { weekday, day, month } = partes(fecha)
  return `${capitalizar(weekday)} ${day} ${month}`
}

export function hora(fecha) {
  return formatoHora.format(aFecha(fecha))
}

// Cuándo es el evento, en una línea:
//   'Hoy · 22:30'                         sin fecha de fin
//   'Sáb 14 nov · 22:30 – 01:00'          termina el mismo día o esa madrugada
//   'Vie 4 dic · 10:00 · hasta Dom 6 dic' dura más de un día
export function cuando(evento, ahora = new Date()) {
  const inicio = `${diaRelativo(evento.fecha_inicio, ahora)} · ${hora(evento.fecha_inicio)}`
  if (!evento.fecha_fin) return inicio
  const duracion = aFecha(evento.fecha_fin) - aFecha(evento.fecha_inicio)
  if (duracion < MS_POR_DIA) return `${inicio} – ${hora(evento.fecha_fin)}`
  return `${inicio} · hasta ${diaRelativo(evento.fecha_fin, ahora)}`
}

const formatoFechaLarga = new Intl.DateTimeFormat(LOCALE, {
  timeZone: ZONA_HORARIA,
  weekday: 'long',
  day: 'numeric',
  month: 'long',
  year: 'numeric',
})

// 'Viernes 13 de noviembre'; con el año solo si no es el actual
// ('Lunes 4 de enero de 2027').
export function fechaLarga(fecha, ahora = new Date()) {
  const p = {}
  for (const { type, value } of formatoFechaLarga.formatToParts(aFecha(fecha))) {
    p[type] = value
  }
  const anio = p.year === claveDia(ahora).slice(0, 4) ? '' : ` de ${p.year}`
  return `${capitalizar(p.weekday)} ${p.day} de ${p.month}${anio}`
}

// Cuándo es el evento, en dos renglones para la ficha de detalle:
//   { principal: 'Viernes 13 de noviembre', secundario: '22:30 – 01:00' }
//   { principal: 'Viernes 4 de diciembre, 10:00',
//     secundario: 'Hasta el domingo 6 de diciembre, 18:00' }  (más de un día)
export function cuandoDetalle(evento, ahora = new Date()) {
  const { fecha_inicio: inicio, fecha_fin: fin } = evento
  if (!fin) return { principal: fechaLarga(inicio, ahora), secundario: hora(inicio) }
  if (aFecha(fin) - aFecha(inicio) < MS_POR_DIA) {
    return { principal: fechaLarga(inicio, ahora), secundario: `${hora(inicio)} – ${hora(fin)}` }
  }
  const finLargo = fechaLarga(fin, ahora)
  return {
    principal: `${fechaLarga(inicio, ahora)}, ${hora(inicio)}`,
    secundario: `Hasta el ${finLargo.charAt(0).toLowerCase()}${finLargo.slice(1)}, ${hora(fin)}`,
  }
}

// Ya pasó: terminó o, si no tiene fecha de fin, ya empezó. El backend igual
// lo muestra (un evento cancelado o terminado se puede seguir consultando).
export function yaTermino(evento, ahora = new Date()) {
  return aFecha(evento.fecha_fin ?? evento.fecha_inicio) < ahora
}

// El precio es opcional (RF-02.1): sin precio no se muestra nada, porque no
// se sabe si es gratis. 0 es 'Gratis'. Llega como texto ("6000.00").
export function precio(valor) {
  if (valor === null || valor === undefined) return null
  const numero = Number(valor)
  return numero === 0 ? 'Gratis' : formatoPrecio.format(numero)
}

// --- <input type="datetime-local"> ---
// El input da y recibe 'YYYY-MM-DDTHH:MM' sin zona. Se interpreta en la zona
// de la plataforma y no en la del navegador: así lo que escribe el
// organizador es lo mismo que después muestran la tarjeta y la ficha.

const formatoPartes = new Intl.DateTimeFormat('en-CA', {
  timeZone: ZONA_HORARIA,
  year: 'numeric',
  month: '2-digit',
  day: '2-digit',
  hour: '2-digit',
  minute: '2-digit',
  hourCycle: 'h23',
})

function partesEnZona(fecha) {
  return Object.fromEntries(
    formatoPartes.formatToParts(fecha).map(({ type, value }) => [type, value]),
  )
}

// Fecha (o texto ISO de la API) -> valor para el input.
export function aValorFechaHora(valor) {
  const { year, month, day, hour, minute } = partesEnZona(aFecha(valor))
  return `${year}-${month}-${day}T${hour}:${minute}`
}

// Diferencia en ms entre la hora de la zona y UTC en un instante dado.
function desfasaje(instante) {
  const { year, month, day, hour, minute } = partesEnZona(new Date(instante))
  const comoUtc = Date.UTC(year, month - 1, day, hour, minute)
  return comoUtc - Math.floor(instante / 60000) * 60000
}

// Valor del input -> Date. La primera estimación usa el desfasaje de esa hora
// tomada como UTC; la segunda corrige si justo cae en un cambio de horario.
export function deValorFechaHora(valor) {
  const [fecha, horaMinutos] = valor.split('T')
  const [anio, mes, dia] = fecha.split('-').map(Number)
  const [horas, minutos] = horaMinutos.split(':').map(Number)
  const comoUtc = Date.UTC(anio, mes - 1, dia, horas, minutos)
  const estimado = comoUtc - desfasaje(comoUtc)
  return new Date(comoUtc - desfasaje(estimado))
}

// true si el navegador está en otra zona: el formulario lo aclara.
export function navegadorEnOtraZona() {
  return Intl.DateTimeFormat().resolvedOptions().timeZone !== ZONA_HORARIA
}
