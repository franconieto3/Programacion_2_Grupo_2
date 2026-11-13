import { useQuery } from '@tanstack/react-query'
import { listarMisEventos } from '../../../services/eventos'
import { clavesEventos } from '../clavesEventos'
import { aFecha, yaTermino } from '../formato'

const SIN_EVENTOS = { eventos: [], proximos: [], finalizados: [] }

// Separa en próximos (el más cercano primero) y finalizados (el más reciente
// primero). Como `select`, corre al llegar los datos y no en cada render.
function separar(eventos) {
  const ahora = new Date()
  const porInicio = (a, b) => aFecha(a.fecha_inicio) - aFecha(b.fecha_inicio)
  return {
    eventos,
    proximos: eventos.filter((e) => !yaTermino(e, ahora)).sort(porInicio),
    finalizados: eventos.filter((e) => yaTermino(e, ahora)).sort((a, b) => porInicio(b, a)),
  }
}

// "Mis eventos" del organizador (RF-02.5), en cualquier estado.
// Devuelve lo mismo que useQuery más { eventos, proximos, finalizados }.
// La clave empieza con 'eventos': crear, editar o cancelar uno la invalida.
export function useMisEventos() {
  const consulta = useQuery({
    queryKey: clavesEventos.mios,
    queryFn: ({ signal }) => listarMisEventos({ signal }),
    select: separar,
  })
  return { ...consulta, ...(consulta.data ?? SIN_EVENTOS) }
}
