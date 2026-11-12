import { useCallback, useEffect, useRef, useState } from "react";
import Icono from "../components/ui/Icono";
import ListaEventos from "../features/eventos/components/ListaEventos";
import MapaEventos from "../features/eventos/components/MapaEventos";
import PanelFiltros from "../features/eventos/components/PanelFiltros";
import { useBusquedaEventos } from "../features/eventos/hooks/useBusquedaEventos";
import { useEstadoExplorar } from "../features/eventos/hooks/useEstadoExplorar";
import { useFiltrosBusqueda } from "../features/eventos/hooks/useFiltrosBusqueda";
import BuscadorLugar from "../features/ubicacion/components/BuscadorLugar";
import { useUbicacionInicial } from "../features/ubicacion/hooks/useUbicacionInicial";
import "./Explorar.css";

// Descubrimiento de eventos (CU-01, CU-02). Mapa y lista muestran la misma
// búsqueda (RF-03.2): useBusquedaEventos con lo que se ve en el mapa y los
// filtros. Desde 1024px van lado a lado; más chico, se alterna entre los dos
// con el botón flotante "Mapa" / "Lista".
//
// Dónde abre el mapa:
// 1. Si la URL trae la posición (se vuelve de la ficha de un evento), ahí.
// 2. Si no, en la ubicación del usuario o, si no la da, en la por defecto
//    del backend con un aviso y el buscador destacado (RF-03.8).
const Explorar = () => {
  const { filtros, cambiar, limpiar, hayFiltros } = useFiltrosBusqueda();
  const { posicionInicial, guardarPosicion, vista, cambiarVista } = useEstadoExplorar();
  const inicial = useUbicacionInicial({ activo: posicionInicial === null });

  // Dónde se montó el mapa. Se fija una sola vez: después se mueve con la
  // instancia de Leaflet (mapaRef).
  const [centro, setCentro] = useState(() =>
    posicionInicial ? { ...posicionInicial, origen: "url" } : null,
  );
  if (!centro && inicial.ubicacion) setCentro({ ...inicial.ubicacion, origen: inicial.origen });

  const [viewport, setViewport] = useState(null);
  const busqueda = useBusquedaEventos(viewport, filtros, { habilitada: viewport !== null });

  const mapaRef = useRef(null);
  const buscadorRef = useRef(null);
  // Si el usuario ya movió el mapa o buscó un lugar, una ubicación que llega
  // tarde no lo saca de donde está.
  const movido = useRef(false);
  const [avisoCerrado, setAvisoCerrado] = useState(false);
  const avisoVisible = inicial.origen === "defecto" && !avisoCerrado;

  // El usuario aceptó el permiso después de que el mapa abrió en la
  // ubicación por defecto: se lo lleva a la suya.
  const { origen, ubicacion } = inicial;
  useEffect(() => {
    if (origen !== "usuario" || centro?.origen !== "defecto" || movido.current) return;
    mapaRef.current?.setView([ubicacion.lat, ubicacion.lng], ubicacion.zoom);
    // Solo cuando cambia el origen: ubicacion es un objeto nuevo en cada render.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [origen]);

  const alCambiarViewport = useCallback(
    (nuevo, { centro: centroMapa, zoom }) => {
      setViewport(nuevo);
      guardarPosicion(centroMapa, zoom);
    },
    [guardarPosicion],
  );

  const alInteractuar = useCallback(() => {
    movido.current = true;
  }, []);

  const irALugar = (lugar) => {
    movido.current = true;
    setAvisoCerrado(true);
    mapaRef.current?.fitBounds(
      [
        [lugar.lat_min, lugar.lng_min],
        [lugar.lat_max, lugar.lng_max],
      ],
      // Una dirección tiene un recuadro de pocos metros: no acercar tanto.
      { maxZoom: 16 },
    );
  };

  const alternarVista = () => {
    cambiarVista(vista === "mapa" ? "lista" : "mapa");
    window.scrollTo({ top: 0 });
  };

  return (
    <div className={`explorar explorar-vista-${vista}`}>
      <div className="explorar-panel">
        <div className="explorar-encabezado">
          <h1 className="explorar-titulo">Explorar</h1>
          <BuscadorLugar ref={buscadorRef} onSeleccionar={irALugar} destacado={avisoVisible} />
          {avisoVisible && (
            <AvisoUbicacion
              nombre={ubicacion.nombre}
              motivo={inicial.motivo}
              onCerrar={(conTeclado) => {
                setAvisoCerrado(true);
                // El botón desaparece: el foco pasa al buscador en vez de
                // perderse. Solo con teclado, para no abrir el teclado del
                // celular al tocar la X.
                if (conTeclado) buscadorRef.current?.focus();
              }}
            />
          )}
          <PanelFiltros
            filtros={filtros}
            onCambiar={cambiar}
            onLimpiar={limpiar}
            hayFiltros={hayFiltros}
          />
        </div>
        <div className="explorar-lista">
          <ListaEventos
            busqueda={busqueda}
            hayFiltros={hayFiltros}
            onLimpiarFiltros={limpiar}
            porZona
          />
        </div>
      </div>

      <div className="explorar-mapa">
        {centro ? (
          <MapaEventos
            ref={mapaRef}
            eventos={busqueda.eventos}
            total={busqueda.total}
            centro={centro}
            onCambioViewport={alCambiarViewport}
            onInteraccion={alInteractuar}
            actualizando={busqueda.actualizando}
            className="explorar-mapa-eventos"
          />
        ) : (
          <div className="explorar-mapa-esqueleto esqueleto" role="status" aria-label="Cargando el mapa" />
        )}
      </div>

      <button type="button" className="explorar-alternar" onClick={alternarVista}>
        <Icono nombre={vista === "mapa" ? "view_list" : "map"} />
        {vista === "mapa" ? "Lista" : "Mapa"}
      </button>
    </div>
  );
};

// RF-03.8: no se pudo usar la ubicación del usuario. No bloquea nada: el
// mapa ya está abierto en la ciudad por defecto y el buscador, destacado.
const TEXTOS_MOTIVO = {
  denegado: "No tenemos permiso para ver tu ubicación",
  "no-soportado": "Tu navegador no comparte la ubicación",
};

// Con el mapa a la vista en el celular se muestra la versión corta, para no
// quitarle lugar al mapa.
const AvisoUbicacion = ({ nombre, motivo, onCerrar }) => (
  <div className="explorar-aviso" role="status">
    <Icono nombre="location_off" className="explorar-aviso-icono" />
    <p className="explorar-aviso-largo">
      {TEXTOS_MOTIVO[motivo] ?? "No pudimos obtener tu ubicación"}: te mostramos{" "}
      <strong>{nombre}</strong>. Buscá tu zona para ver eventos cerca tuyo.
    </p>
    <p className="explorar-aviso-corto">
      Sin tu ubicación: te mostramos <strong>{nombre}</strong>.
    </p>
    <button
      type="button"
      className="explorar-aviso-cerrar"
      aria-label="Cerrar el aviso"
      // detail es 0 cuando el click viene del teclado (Enter o espacio).
      onClick={(evento) => onCerrar(evento.detail === 0)}
    >
      <Icono nombre="close" />
    </button>
  </div>
);

export default Explorar;
