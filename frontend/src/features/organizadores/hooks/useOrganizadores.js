import { useQuery } from '@tanstack/react-query'
import { listarOrganizadores } from '../../../services/organizadores'

// Claves de caché de la administración de organizadores. Después de aprobar,
// rechazar o suspender, invalidar `todas`: el organizador cambia de pestaña.
export const clavesOrganizadores = {
  todas: ['organizadores'],
  porEstado: (estado) => ['organizadores', estado],
}

// Perfiles de organizador en un estado (RF-05.5), los más antiguos primero.
// Solo administradores (AdminRoute).
export function useOrganizadores(estado) {
  return useQuery({
    queryKey: clavesOrganizadores.porEstado(estado),
    queryFn: ({ signal }) => listarOrganizadores(estado, { signal }),
  })
}
