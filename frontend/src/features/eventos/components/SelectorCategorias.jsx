import Icono from "../../../components/ui/Icono";
import { useCategorias } from "../hooks/useCategorias";
import "./SelectorCategorias.css";

// Chips para elegir una o varias categorías del catálogo (RF-03.6, RF-02.3).
// Muestra `nombre` y trabaja con `slug`, que es lo que espera la API.
// - seleccionadas: lista de slugs. onChange(slugs) con la lista nueva.
// - etiqueta: nombre del grupo para los lectores de pantalla.
// - desplazable: en una sola fila con scroll horizontal en el celular (para
//   los filtros); si no, los chips bajan de línea (para un formulario).
// En los filtros, ninguna seleccionada significa "todas".
const SelectorCategorias = ({
  seleccionadas = [],
  onChange,
  etiqueta = "Categorías",
  desplazable = false,
  className = "",
}) => {
  const { data: categorias, isPending, isError, refetch } = useCategorias();
  const clases = `selector-categorias ${desplazable ? "selector-categorias-desplazable" : ""} ${className}`.trim();

  if (isPending) {
    return (
      <div className={clases} aria-hidden="true">
        {[5, 7, 4, 6, 8].map((ancho, i) => (
          <span key={i} className="chip chip-esqueleto" style={{ width: `${ancho}rem` }} />
        ))}
      </div>
    );
  }

  if (isError) {
    return (
      <p className="selector-categorias-error">
        No pudimos cargar las categorías.{" "}
        <button type="button" className="selector-categorias-reintentar" onClick={() => refetch()}>
          Reintentar
        </button>
      </p>
    );
  }

  const alternar = (slug) =>
    onChange(
      seleccionadas.includes(slug)
        ? seleccionadas.filter((s) => s !== slug)
        : [...seleccionadas, slug],
    );

  return (
    <div className={clases} role="group" aria-label={etiqueta}>
      {categorias.map(({ slug, nombre, descripcion }) => {
        const activa = seleccionadas.includes(slug);
        return (
          <button
            key={slug}
            type="button"
            className={`chip ${activa ? "chip-activo" : ""}`.trim()}
            aria-pressed={activa}
            title={descripcion ?? undefined}
            onClick={() => alternar(slug)}
          >
            {activa && <Icono nombre="check" />}
            {nombre}
          </button>
        );
      })}
    </div>
  );
};

export default SelectorCategorias;
