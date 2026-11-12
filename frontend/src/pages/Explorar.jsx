import ListaEventos from "../features/eventos/components/ListaEventos";
import PanelFiltros from "../features/eventos/components/PanelFiltros";
import { useBusquedaEventos } from "../features/eventos/hooks/useBusquedaEventos";
import { useFiltrosBusqueda } from "../features/eventos/hooks/useFiltrosBusqueda";
import "./Explorar.css";

// Descubrimiento de eventos (CU-01). Por ahora solo la lista con los filtros
// (etapa 2, paso 3); el mapa se suma en el paso 7 con el mismo
// useBusquedaEventos y su viewport en lugar de null.
const Explorar = () => {
  const { filtros, cambiar, limpiar, hayFiltros } = useFiltrosBusqueda();
  const busqueda = useBusquedaEventos(null, filtros);

  return (
    <div className="pagina">
      <h1 className="pagina-titulo">Explorar</h1>
      <PanelFiltros
        filtros={filtros}
        onCambiar={cambiar}
        onLimpiar={limpiar}
        hayFiltros={hayFiltros}
      />
      <div className="explorar-resultados">
        <ListaEventos busqueda={busqueda} hayFiltros={hayFiltros} onLimpiarFiltros={limpiar} />
      </div>
    </div>
  );
};

export default Explorar;
