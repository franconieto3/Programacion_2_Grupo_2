// Claves de caché de TanStack Query para los eventos. Todas empiezan con
// 'eventos': después de crear, editar o cancelar un evento alcanza con
// queryClient.invalidateQueries({ queryKey: clavesEventos.todas }) para que
// el mapa, la lista y el detalle se vuelvan a pedir.
export const clavesEventos = {
  todas: ['eventos'],
  busqueda: (parametros, tamanoPagina) => [
    'eventos',
    'busqueda',
    parametros,
    tamanoPagina,
  ],
  detalle: (idEvento) => ['eventos', 'detalle', idEvento],
  mios: ['eventos', 'mios'],
}
