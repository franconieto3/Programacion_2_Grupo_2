import { useQuery } from '@tanstack/react-query'
import { listarCategorias } from '../../../services/categorias'

// Catálogo de categorías (RF-04.1), compartido por los filtros, el formulario
// de eventos y las tarjetas. Casi no cambia: se pide una vez por sesión.
export function useCategorias() {
  return useQuery({
    queryKey: ['categorias'],
    queryFn: ({ signal }) => listarCategorias({ signal }),
    staleTime: Infinity,
  })
}
