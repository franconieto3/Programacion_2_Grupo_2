import { useId, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import Icono from "../../../components/ui/Icono";
import Spinner from "../../../components/ui/Spinner";
import { useDebounce } from "../../../hooks/useDebounce";
import { buscarLugar, MIN_CARACTERES_BUSQUEDA } from "../../../services/geocodificacion";
import "./BuscadorLugar.css";

// Buscador de lugares (RF-03.7, CU-02): sugerencias mientras se escribe y,
// al elegir una, onSeleccionar(lugar) con { nombre, lat, lng, lat_min,
// lat_max, lng_min, lng_max } para que la página mueva el mapa
// (map.fitBounds). Sigue el patrón "combobox" de ARIA: flechas para recorrer
// las sugerencias, Enter para elegir, Escape para cerrar o borrar.
//
// Busca desde MIN_CARACTERES_BUSQUEDA letras y medio segundo después de la
// última tecla: el backend consulta Nominatim, que admite 1 request por
// segundo. Si se sigue escribiendo, la búsqueda anterior se cancela.
// - destacado: más grande y con sombra, para cuando no hay ubicación del
//   usuario (RF-03.8) y buscar es la forma de llegar a su zona.
// - ref: el <input>, para darle el foco desde afuera.
const ESPERA = 500;

const BuscadorLugar = ({ onSeleccionar, destacado = false, className = "", ref }) => {
  const [texto, setTexto] = useState("");
  const [abierto, setAbierto] = useState(false);
  const [activa, setActiva] = useState(-1);
  // Nombre del último lugar elegido: al ponerlo en el input no tiene que
  // dispararse otra búsqueda ni abrirse la lista.
  const [elegido, setElegido] = useState(null);
  const id = useId();
  const idLista = `${id}-sugerencias`;

  const consulta = useDebounce(texto.trim(), ESPERA);
  const yaElegido = elegido !== null && texto.trim() === elegido;
  const suficiente = consulta.length >= MIN_CARACTERES_BUSQUEDA && consulta !== elegido;
  const { data: lugares = [], isFetching, isError, error } = useQuery({
    queryKey: ["geocodificacion", consulta.toLowerCase()],
    queryFn: ({ signal }) => buscarLugar(consulta, { signal }),
    enabled: suficiente,
    staleTime: 5 * 60 * 1000,
    // Un 503 de Nominatim no se reintenta solo: con el límite de 1 por
    // segundo, reintentar empeora las cosas. Se reintenta al seguir escribiendo.
    retry: false,
    // Sin keepPreviousData: mientras busca muestra "Buscando..." y no las
    // sugerencias de lo que se había escrito antes, que confundirían.
  });

  // Lo que se escribe todavía no se buscó (debounce) o está en camino.
  const pendiente = !yaElegido && (texto.trim() !== consulta || isFetching);
  const mostrarLista =
    abierto && suficiente && !yaElegido && texto.trim().length >= MIN_CARACTERES_BUSQUEDA;
  // Mientras corre el debounce, las sugerencias en pantalla son de lo escrito
  // antes: se muestran solo si lo nuevo las refina ("Rosa" -> "Rosario").
  const vigentes = texto.trim().toLowerCase().startsWith(consulta.toLowerCase());
  const opciones = mostrarLista && !isError && vigentes ? lugares : [];

  const elegir = (lugar) => {
    const nombre = nombreCorto(lugar.nombre);
    setTexto(nombre);
    setElegido(nombre);
    setAbierto(false);
    setActiva(-1);
    onSeleccionar(lugar);
  };

  const alPresionar = (evento) => {
    if (evento.key === "ArrowDown" || evento.key === "ArrowUp") {
      evento.preventDefault();
      if (!abierto) setAbierto(true);
      if (opciones.length === 0) return;
      const paso = evento.key === "ArrowDown" ? 1 : -1;
      setActiva((actual) => (actual + paso + opciones.length) % opciones.length);
    } else if (evento.key === "Enter") {
      if (!mostrarLista) return;
      evento.preventDefault();
      const lugar = opciones[activa] ?? opciones[0];
      if (lugar) elegir(lugar);
    } else if (evento.key === "Escape") {
      // Sin esto, Chrome borra un <input type="search"> con Escape.
      evento.preventDefault();
      if (mostrarLista) setAbierto(false);
      else setTexto("");
      setActiva(-1);
    }
  };

  return (
    <div
      className={`buscador-lugar ${destacado ? "buscador-lugar-destacado" : ""} ${className}`.trim()}
      onBlur={(evento) => {
        if (!evento.currentTarget.contains(evento.relatedTarget)) setAbierto(false);
      }}
    >
      <label htmlFor={id} className="sr-only">
        Buscar un lugar
      </label>
      <Icono nombre="search" className="buscador-lugar-lupa" />
      <input
        ref={ref}
        id={id}
        type="search"
        className="buscador-lugar-input"
        placeholder="Buscar un barrio, ciudad o dirección"
        autoComplete="off"
        spellCheck={false}
        role="combobox"
        aria-expanded={mostrarLista}
        aria-controls={idLista}
        aria-autocomplete="list"
        aria-activedescendant={activa >= 0 && opciones[activa] ? `${idLista}-${activa}` : undefined}
        value={texto}
        onChange={(evento) => {
          setTexto(evento.target.value);
          setAbierto(true);
          setActiva(-1);
        }}
        onFocus={() => setAbierto(true)}
        onKeyDown={alPresionar}
      />
      {texto && pendiente && suficiente && (
        <Spinner tamano="sm" decorativo className="buscador-lugar-spinner" />
      )}
      {texto && (
        <button
          type="button"
          className="buscador-lugar-borrar"
          aria-label="Borrar la búsqueda"
          onClick={(evento) => {
            setTexto("");
            setActiva(-1);
            evento.currentTarget.parentElement.querySelector("input").focus();
          }}
        >
          <Icono nombre="close" />
        </button>
      )}

      <div className="buscador-lugar-panel" hidden={!mostrarLista}>
        <ul id={idLista} role="listbox" aria-label="Sugerencias" className="buscador-lugar-lista">
          {opciones.map((lugar, indice) => {
            const [principal, ...resto] = lugar.nombre.split(", ");
            return (
              <li
                key={`${lugar.lat},${lugar.lng},${lugar.nombre}`}
                id={`${idLista}-${indice}`}
                role="option"
                aria-selected={indice === activa}
                className="buscador-lugar-opcion"
                // mousedown en vez de click: el input no pierde el foco antes.
                onMouseDown={(evento) => {
                  evento.preventDefault();
                  elegir(lugar);
                }}
                // mousemove y no mouseenter: si la lista aparece debajo del
                // puntero quieto, no tiene que marcar una opción sola.
                onMouseMove={() => indice !== activa && setActiva(indice)}
              >
                <Icono nombre="location_on" />
                <span className="buscador-lugar-opcion-texto">
                  <span className="buscador-lugar-opcion-principal">{principal}</span>
                  {resto.length > 0 && (
                    <span className="buscador-lugar-opcion-detalle">{resto.join(", ")}</span>
                  )}
                </span>
              </li>
            );
          })}
        </ul>
        <p className="buscador-lugar-mensaje" role="status">
          {mensaje({ isError, error, pendiente, cantidad: opciones.length, consulta })}
        </p>
      </div>
    </div>
  );
};

// Texto bajo las sugerencias; también lo anuncian los lectores de pantalla.
function mensaje({ isError, error, pendiente, cantidad, consulta }) {
  if (isError) {
    return error?.status === 503
      ? "El buscador de lugares no está disponible. Probá de nuevo en unos segundos."
      : "No pudimos buscar el lugar. Probá de nuevo.";
  }
  if (pendiente && cantidad === 0) return "Buscando...";
  if (cantidad === 0) return `No encontramos lugares para "${consulta}".`;
  return "";
}

// "Córdoba, Municipio de Córdoba, ..., Argentina" -> "Córdoba".
function nombreCorto(nombre) {
  return nombre.split(", ")[0];
}

export default BuscadorLugar;
