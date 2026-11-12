import { useQuery } from '@tanstack/react-query'
import { obtenerEvento } from '../../../services/eventos'
import { clavesEventos } from '../clavesEventos'

const FORMATO_UUID =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i

// Ficha de un evento (RF-03.10): el evento con su organizador.
// Devuelve lo mismo que useQuery más `noEncontrado`: true si el id no tiene
// formato de UUID (ni se pide) o si el backend responde 404 (no existe, está
// oculto o es un borrador ajeno). Un 404 no se reintenta (ver queryClient.js).
export function useEvento(idEvento) {
  const idValido = FORMATO_UUID.test(idEvento ?? '')
  const consulta = useQuery({
    queryKey: clavesEventos.detalle(idEvento),
    queryFn: ({ signal }) => obtenerEvento(idEvento, { signal }),
    enabled: idValido,
  })
  return {
    ...consulta,
    noEncontrado: !idValido || consulta.error?.status === 404,
  }
}
