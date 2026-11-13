import { useEffect, useId, useRef, useState } from "react";
import FormError from "../../../components/ui/FormError";
import FormField from "../../../components/ui/FormField";
import Input from "../../../components/ui/Input";
import SubmitButton from "../../../components/ui/SubmitButton";
import Textarea from "../../../components/ui/Textarea";
import { useFormSubmit } from "../../../hooks/useFormSubmit";
import SelectorUbicacion from "../../ubicacion/components/SelectorUbicacion";
import {
  aValorFechaHora,
  deValorFechaHora,
  navegadorEnOtraZona,
  ZONA_HORARIA,
} from "../formato";
import SelectorCategorias from "./SelectorCategorias";
import "./FormularioEvento.css";

// Límites del backend (CrearEventoRequest): título y datos del lugar hasta
// 255 caracteres; precio con 10 dígitos y 2 decimales. La descripción no
// tiene tope en la API: el de acá es para que la ficha se pueda leer.
const MAX_TEXTO = 255;
const MAX_DESCRIPCION = 2000;
const PRECIO_MAXIMO = 99999999.99;

// Formulario de un evento (RF-02.1 a RF-02.3), para el alta y la edición.
//
//   <FormularioEvento inicial={evento} onEnviar={async (datos) => ...} textoEnviar="Publicar evento" />
//
// - inicial: el evento como lo devuelve la API (edición) o nada (alta).
// - onEnviar(datos): recibe el cuerpo completo para la API, con fechas en
//   ISO, `precio` y `fecha_fin` en null si quedaron vacíos y `lugar` con sus
//   coordenadas. La edición puede compararlo con `inicial` y mandar solo lo
//   que cambió. Si lanza un ApiError, se muestra en el formulario.
// - children: acciones extra junto al botón de enviar (p. ej. "Descartar").
const FormularioEvento = ({
  inicial,
  onEnviar,
  textoEnviar = "Guardar",
  textoEnviando = "Guardando...",
  children,
}) => {
  const formRef = useRef(null);
  const id = useId();
  const [categorias, setCategorias] = useState(() => inicial?.categorias.map((c) => c.slug) ?? []);
  const [punto, setPunto] = useState(() =>
    inicial ? { latitud: inicial.lugar.latitud, longitud: inicial.lugar.longitud } : null,
  );
  const [nombreLugar, setNombreLugar] = useState(inicial?.lugar.nombre ?? "");
  const [direccion, setDireccion] = useState(inicial?.lugar.direccion ?? "");
  // Lo último que se completó solo desde el buscador: si el usuario no lo
  // tocó, otra búsqueda lo puede reemplazar; lo que escribió él, no.
  const sugerido = useRef({ nombre: "", direccion: "" });

  const inicioInicial = inicial ? aValorFechaHora(inicial.fecha_inicio) : "";
  const [inicio, setInicio] = useState(inicioInicial);
  // Para el alta, el inicio no puede ser pasado (el backend responde 422).
  const [ahora] = useState(() => aValorFechaHora(new Date()));

  const validar = (datos) => {
    const errores = {};
    if (!datos.titulo.trim()) errores.titulo = "Ingresá un título.";
    if (!datos.descripcion.trim()) errores.descripcion = "Contá de qué se trata el evento.";
    // En la edición, un inicio que no se tocó puede haber quedado en el pasado.
    const inicioCambio = datos.fecha_inicio !== inicioInicial;
    if (datos.fecha_inicio && inicioCambio && deValorFechaHora(datos.fecha_inicio) <= new Date()) {
      errores.fecha_inicio = "La fecha de inicio tiene que ser futura.";
    }
    if (
      datos.fecha_fin &&
      datos.fecha_inicio &&
      deValorFechaHora(datos.fecha_fin) <= deValorFechaHora(datos.fecha_inicio)
    ) {
      errores.fecha_fin = "Tiene que ser posterior al inicio.";
    }
    if (categorias.length === 0) errores.categorias = "Elegí al menos una categoría.";
    if (!punto) errores.lugar = "Marcá en el mapa dónde es el evento.";
    return errores;
  };

  const { submit, enviando, errores, errorGeneral } = useFormSubmit(
    (datos) =>
      onEnviar({
        titulo: datos.titulo.trim(),
        descripcion: datos.descripcion.trim(),
        fecha_inicio: deValorFechaHora(datos.fecha_inicio).toISOString(),
        fecha_fin: datos.fecha_fin ? deValorFechaHora(datos.fecha_fin).toISOString() : null,
        precio: datos.precio === "" ? null : datos.precio,
        lugar: {
          latitud: punto.latitud,
          longitud: punto.longitud,
          nombre: nombreLugar.trim() || null,
          direccion: direccion.trim() || null,
        },
        categorias,
      }),
    { validar },
  );

  // Después de un envío con errores, se lleva la vista al primero (el
  // formulario es largo y puede haber quedado arriba o abajo).
  useEffect(() => {
    if (Object.keys(errores).length === 0 && !errorGeneral) return;
    formRef.current
      ?.querySelector(".form-field-error, .form-error")
      ?.scrollIntoView({ behavior: "smooth", block: "center" });
  }, [errores, errorGeneral]);

  const alCambiarPunto = (nuevo, { lugar }) => {
    setPunto(nuevo);
    if (!lugar) return;
    // Del buscador: se completan nombre y dirección si están vacíos o si
    // todavía tienen lo que se completó solo la vez anterior.
    const sugerencia = sugerenciaDeLugar(lugar.nombre);
    if (!nombreLugar || nombreLugar === sugerido.current.nombre) {
      setNombreLugar(sugerencia.nombre);
      sugerido.current.nombre = sugerencia.nombre;
    }
    if (!direccion || direccion === sugerido.current.direccion) {
      setDireccion(sugerencia.direccion);
      sugerido.current.direccion = sugerencia.direccion;
    }
  };

  const ayudaZona = navegadorEnOtraZona()
    ? `Hora de ${ZONA_HORARIA.split("/").pop().replaceAll("_", " ")}, como se muestra en la app.`
    : undefined;

  return (
    <form ref={formRef} className="formulario-evento" onSubmit={submit}>
      <section className="formulario-evento-seccion" aria-labelledby={`${id}-datos`}>
        <h2 id={`${id}-datos`} className="formulario-evento-titulo">
          El evento
        </h2>
        <FormField label="Título" error={errores.titulo}>
          <Input
            name="titulo"
            defaultValue={inicial?.titulo}
            placeholder="Ej.: Feria de diseño en el parque"
            maxLength={MAX_TEXTO}
            required
          />
        </FormField>
        <FormField label="Descripción" error={errores.descripcion}>
          <Textarea
            name="descripcion"
            defaultValue={inicial?.descripcion}
            placeholder="Qué va a pasar, para quién es, qué hay que llevar..."
            maxLength={MAX_DESCRIPCION}
            rows={5}
            contador
            required
          />
        </FormField>
        <fieldset className="formulario-evento-grupo">
          <legend className="form-field-label">Categorías</legend>
          <SelectorCategorias
            seleccionadas={categorias}
            onChange={setCategorias}
            etiqueta="Categorías del evento"
          />
          {errores.categorias && <p className="form-field-error">{errores.categorias}</p>}
        </fieldset>
      </section>

      <section className="formulario-evento-seccion" aria-labelledby={`${id}-cuando`}>
        <h2 id={`${id}-cuando`} className="formulario-evento-titulo">
          Cuándo y cuánto
        </h2>
        <div className="formulario-evento-fila">
          <FormField label="Empieza" error={errores.fecha_inicio} ayuda={ayudaZona}>
            <Input
              name="fecha_inicio"
              type="datetime-local"
              defaultValue={inicioInicial}
              min={inicial ? undefined : ahora}
              onChange={(evento) => setInicio(evento.target.value)}
              required
            />
          </FormField>
          <FormField label="Termina (opcional)" error={errores.fecha_fin}>
            <Input
              name="fecha_fin"
              type="datetime-local"
              defaultValue={inicial?.fecha_fin ? aValorFechaHora(inicial.fecha_fin) : ""}
              min={inicio || undefined}
            />
          </FormField>
        </div>
        <FormField
          label="Precio (opcional)"
          error={errores.precio}
          ayuda="En pesos. Poné 0 si es gratis; si lo dejás vacío, no se muestra precio."
          className="formulario-evento-precio"
        >
          <Input
            name="precio"
            type="number"
            inputMode="decimal"
            min="0"
            max={PRECIO_MAXIMO}
            step="0.01"
            defaultValue={inicial?.precio ?? ""}
            placeholder="Sin precio"
          />
        </FormField>
      </section>

      <section className="formulario-evento-seccion" aria-labelledby={`${id}-donde`}>
        <h2 id={`${id}-donde`} className="formulario-evento-titulo">
          Dónde
        </h2>
        <SelectorUbicacion
          valor={punto}
          onCambiar={alCambiarPunto}
          error={errores.lugar}
          etiqueta="Lugar en el mapa"
        />
        <div className="formulario-evento-fila">
          <FormField label="Nombre del lugar (opcional)">
            <Input
              value={nombreLugar}
              onChange={(evento) => setNombreLugar(evento.target.value)}
              placeholder="Ej.: Parque Centenario"
              maxLength={MAX_TEXTO}
            />
          </FormField>
          <FormField label="Dirección (opcional)">
            <Input
              value={direccion}
              onChange={(evento) => setDireccion(evento.target.value)}
              placeholder="Ej.: Av. Díaz Vélez 4800"
              maxLength={MAX_TEXTO}
              autoComplete="street-address"
            />
          </FormField>
        </div>
      </section>

      <FormError mensaje={errorGeneral} />
      <div className="formulario-evento-acciones">
        <SubmitButton enviando={enviando} textoEnviando={textoEnviando}>
          {textoEnviar}
        </SubmitButton>
        {children}
      </div>
    </form>
  );
};

// Nombre y dirección a partir del nombre largo de Nominatim:
// - "1500, Avenida Corrientes, San Nicolás, ..." -> dirección "Avenida Corrientes 1500".
// - "Teatro Colón, 621, Cerrito, San Nicolás, ..." -> nombre "Teatro Colón" y
//   dirección "Cerrito 621".
// - Otro caso ("Parque Centenario, Caballito, ...") -> nombre "Parque Centenario".
const ES_ALTURA = /^\d+[a-zA-Z]?$/;

function sugerenciaDeLugar(nombreCompleto) {
  const partes = nombreCompleto.split(", ");
  if (ES_ALTURA.test(partes[0]) && partes[1]) {
    return { nombre: "", direccion: recortar(`${partes[1]} ${partes[0]}`) };
  }
  if (ES_ALTURA.test(partes[1] ?? "") && partes[2]) {
    return { nombre: recortar(partes[0]), direccion: recortar(`${partes[2]} ${partes[1]}`) };
  }
  return { nombre: recortar(partes[0]), direccion: "" };
}

function recortar(texto) {
  return texto.slice(0, MAX_TEXTO);
}

export default FormularioEvento;
