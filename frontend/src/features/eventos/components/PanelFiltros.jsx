import { useId, useState } from "react";
import Button from "../../../components/ui/Button";
import FormField from "../../../components/ui/FormField";
import Icono from "../../../components/ui/Icono";
import Input from "../../../components/ui/Input";
import { bloqueFecha } from "../formato";
import SelectorCategorias from "./SelectorCategorias";
import "./PanelFiltros.css";

// Filtros del descubrimiento: categorías (RF-03.6) siempre a la vista, y
// fechas (RF-03.4) y horario (RF-03.5) en una sección que se despliega. Cada
// cambio se aplica enseguida, sin botón "Aplicar".
// - filtros: los de useFiltrosBusqueda(). onCambiar(cambios), onLimpiar().
const PanelFiltros = ({ filtros, onCambiar, onLimpiar, hayFiltros }) => {
  const { desde, hasta, hora_desde, hora_hasta, categorias } = filtros;
  const fechaHoraActivos = Boolean(desde || hasta || hora_desde || hora_hasta);
  const [abierto, setAbierto] = useState(fechaHoraActivos);
  const idSeccion = useId();
  const cruzaMedianoche = hora_desde && hora_hasta && hora_desde > hora_hasta;

  // Si "desde" queda después de "hasta", "hasta" se borra en vez de dejar un
  // rango imposible (el backend lo rechazaría).
  const cambiarDesde = (valor) =>
    onCambiar(hasta && valor > hasta ? { desde: valor, hasta: "" } : { desde: valor });

  return (
    <section className="panel-filtros" aria-label="Filtros">
      <SelectorCategorias
        seleccionadas={categorias}
        onChange={(slugs) => onCambiar({ categorias: slugs })}
        etiqueta="Filtrar por categoría"
        desplazable
      />

      <div className="panel-filtros-barra">
        <button
          type="button"
          className={`panel-filtros-toggle ${fechaHoraActivos ? "panel-filtros-toggle-activo" : ""}`.trim()}
          aria-expanded={abierto}
          aria-controls={idSeccion}
          onClick={() => setAbierto((valor) => !valor)}
        >
          <Icono nombre="calendar_today" />
          <span>{resumenFechaHora(filtros) ?? "Fecha y horario"}</span>
          <Icono nombre="expand_more" className="panel-filtros-chevron" />
        </button>
        {hayFiltros && (
          <Button variant="ghost" size="sm" onClick={onLimpiar}>
            Limpiar filtros
          </Button>
        )}
      </div>

      <div id={idSeccion} className="panel-filtros-seccion" hidden={!abierto}>
        <fieldset className="panel-filtros-grupo">
          <legend>Fechas</legend>
          <FormField label="Desde">
            <Input
              type="date"
              value={desde}
              max={hasta || undefined}
              onChange={(e) => cambiarDesde(e.target.value)}
            />
          </FormField>
          <FormField label="Hasta">
            <Input
              type="date"
              value={hasta}
              min={desde || undefined}
              onChange={(e) => onCambiar({ hasta: e.target.value })}
            />
          </FormField>
        </fieldset>

        <fieldset className="panel-filtros-grupo">
          <legend>Hora de inicio</legend>
          <FormField label="Desde">
            <Input
              type="time"
              value={hora_desde}
              onChange={(e) => onCambiar({ hora_desde: e.target.value })}
            />
          </FormField>
          <FormField label="Hasta">
            <Input
              type="time"
              value={hora_hasta}
              onChange={(e) => onCambiar({ hora_hasta: e.target.value })}
            />
          </FormField>
          {cruzaMedianoche && (
            <p className="panel-filtros-ayuda">
              Cruza la medianoche: incluye los que empiezan desde las {hora_desde} o
              hasta las {hora_hasta}.
            </p>
          )}
        </fieldset>
      </div>
    </section>
  );
};

// Texto del botón con los filtros de fecha y hora activos, p. ej.
// "14 nov – 20 nov · 20:00 a 23:00". null si no hay ninguno.
function resumenFechaHora({ desde, hasta, hora_desde, hora_hasta }) {
  // Mediodía UTC: el mismo día en cualquier zona horaria de América.
  const dia = (fecha) => {
    const { dia: numero, mes } = bloqueFecha(`${fecha}T12:00:00Z`);
    return `${numero} ${mes.toLowerCase()}`;
  };
  const rango = (inicio, fin, formato) => {
    if (inicio && fin) return inicio === fin ? formato(inicio) : `${formato(inicio)} – ${formato(fin)}`;
    if (inicio) return `Desde ${formato(inicio)}`;
    if (fin) return `Hasta ${formato(fin)}`;
    return null;
  };
  const partes = [
    rango(desde, hasta, dia),
    rango(hora_desde, hora_hasta, (h) => h)?.replace(" – ", " a "),
  ].filter(Boolean);
  return partes.length ? partes.join(" · ") : null;
}

export default PanelFiltros;
