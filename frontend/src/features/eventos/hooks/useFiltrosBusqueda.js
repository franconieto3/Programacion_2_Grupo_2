import { useCallback, useMemo } from 'react'
import { useSearchParams } from 'react-router-dom'

// Filtros de la búsqueda guardados en la URL (?desde=2026-11-14&categorias=bar
// &categorias=teatro): sobreviven a una recarga, se pueden compartir y el
// botón "atrás" del navegador no los pierde.
//
//   const { filtros, cambiar, limpiar, hayFiltros } = useFiltrosBusqueda()
//   cambiar({ desde: '2026-11-14' })   // '' o [] borra el filtro
//
// filtros: { desde, hasta, hora_desde, hora_hasta, categorias } con los
// mismos nombres que buscarEventos(). Los valores mal formados de la URL
// (escrita a mano o vieja) se ignoran, para no terminar en un 422.

const CLAVES = ['desde', 'hasta', 'hora_desde', 'hora_hasta', 'categorias']
const FORMATO_FECHA = /^\d{4}-\d{2}-\d{2}$/
const FORMATO_HORA = /^([01]\d|2[0-3]):[0-5]\d$/

function fechaValida(valor) {
  if (!FORMATO_FECHA.test(valor ?? '')) return ''
  // Descarta fechas que no existen, como 2026-02-31.
  const fecha = new Date(`${valor}T00:00:00Z`)
  return !Number.isNaN(fecha.getTime()) && fecha.toISOString().startsWith(valor)
    ? valor
    : ''
}

const horaValida = (valor) => (FORMATO_HORA.test(valor ?? '') ? valor : '')

export function leerFiltros(params) {
  const desde = fechaValida(params.get('desde'))
  let hasta = fechaValida(params.get('hasta'))
  if (desde && hasta && desde > hasta) hasta = ''
  return {
    desde,
    hasta,
    hora_desde: horaValida(params.get('hora_desde')),
    hora_hasta: horaValida(params.get('hora_hasta')),
    categorias: [...new Set(params.getAll('categorias'))],
  }
}

export function useFiltrosBusqueda() {
  const [params, setParams] = useSearchParams()
  const filtros = useMemo(() => leerFiltros(params), [params])

  // `replace`: cambiar un filtro no agrega una entrada al historial, así
  // "atrás" vuelve a la página anterior y no al filtro anterior.
  const cambiar = useCallback(
    (cambios) =>
      setParams(
        (anteriores) => {
          const siguientes = new URLSearchParams(anteriores)
          for (const [clave, valor] of Object.entries(cambios)) {
            siguientes.delete(clave)
            for (const item of [valor].flat()) {
              if (item) siguientes.append(clave, item)
            }
          }
          return siguientes
        },
        { replace: true },
      ),
    [setParams],
  )

  const limpiar = useCallback(
    () => cambiar(Object.fromEntries(CLAVES.map((clave) => [clave, '']))),
    [cambiar],
  )

  const hayFiltros =
    Boolean(
      filtros.desde || filtros.hasta || filtros.hora_desde || filtros.hora_hasta,
    ) || filtros.categorias.length > 0

  return { filtros, cambiar, limpiar, hayFiltros }
}
