import { useCallback, useEffect, useId, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { useRanuraBarra } from "../components/layout/ranuraBarra";
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

// Descubrimiento de eventos (CU-01, CU-02), map-first: el mapa ocupa todo el
// alto debajo de la barra y mapa y lista muestran la misma búsqueda
// (RF-03.2): useBusquedaEventos con lo que se ve en el mapa y los filtros.
// - El buscador de lugares va en el centro de la barra superior (portal a la
//   ranura del Layout) y mueve el mapa.
// - Desde 1024px, filtros y resultados van en un panel flotante a la
//   izquierda, que se puede colapsar para ver solo el mapa.
// - Más chico, se ve el mapa y la lista se abre encima con el botón flotante
//   "Lista" / "Mapa" (?vista=lista).
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
  // Panel de resultados en pantallas anchas (en el celular manda `vista`).
  const [panelAbierto, setPanelAbierto] = useState(true);
  const botonColapsarRef = useRef(null);
  const botonAbrirRef = useRef(null);
  const idPanel = useId();
  const ranura = useRanuraBarra();
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

  // Al colapsar o abrir el panel, el foco pasa al botón que queda visible.
  const colapsarPanel = () => {
    setPanelAbierto(false);
    requestAnimationFrame(() => botonAbrirRef.current?.focus());
  };
  const abrirPanel = () => {
    setPanelAbierto(true);
    requestAnimationFrame(() => botonColapsarRef.current?.focus());
  };

  const buscador = (
    <BuscadorLugar ref={buscadorRef} onSeleccionar={irALugar} destacado={avisoVisible} />
  );

  // "12 eventos" para los botones que abren la lista (null mientras carga).
  const textoTotal = busqueda.cargando
    ? null
    : `${busqueda.total} ${busqueda.total === 1 ? "evento" : "eventos"}`;

  return (
    <div
      className={[
        "explorar",
        `explorar-vista-${vista}`,
        panelAbierto ? "explorar-panel-abierto" : "explorar-panel-cerrado",
      ].join(" ")}
    >
      <h1 className="sr-only">Explorar eventos</h1>

      {/* El buscador va en la barra superior; fuera del layout, sobre el mapa. */}
      {ranura ? (
        createPortal(buscador, ranura)
      ) : (
        <div className="explorar-buscador-flotante">{buscador}</div>
      )}

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

      <aside id={idPanel} className="explorar-panel" aria-label="Filtros y resultados">
        <div className="explorar-panel-encabezado">
          <h2 className="explorar-panel-titulo">Eventos en esta zona</h2>
          <button
            ref={botonColapsarRef}
            type="button"
            className="explorar-panel-colapsar"
            aria-label="Ocultar la lista y ver solo el mapa"
            aria-controls={idPanel}
            aria-expanded={panelAbierto}
            title="Ocultar la lista"
            onClick={colapsarPanel}
          >
            <Icono nombre="left_panel_close" />
          </button>
        </div>
        <div className="explorar-panel-filtros">
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
      </aside>

      {/* Pantallas anchas, con el panel colapsado: tarjeta para volver a abrirlo. */}
      {!panelAbierto && (
        <button
          ref={botonAbrirRef}
          type="button"
          className="explorar-panel-abrir"
          aria-controls={idPanel}
          aria-expanded={false}
          onClick={abrirPanel}
        >
          <Icono nombre="left_panel_open" />
          <span>
            Ver lista
            {textoTotal && <span className="explorar-panel-abrir-total">{textoTotal}</span>}
          </span>
          {hayFiltros && <span className="explorar-panel-abrir-filtros">Con filtros</span>}
        </button>
      )}

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

      {/* Celular: alterna entre el mapa y la lista. */}
      <button type="button" className="explorar-alternar" onClick={alternarVista}>
        <Icono nombre={vista === "mapa" ? "view_list" : "map"} />
        {vista === "mapa" ? ["Lista", textoTotal].filter(Boolean).join(" · ") : "Mapa"}
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

// Tarjeta flotante sobre el mapa. En el celular se muestra la versión corta,
// para no quitarle lugar al mapa.
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
