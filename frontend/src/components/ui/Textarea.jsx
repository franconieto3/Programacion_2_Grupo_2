import { useContext, useId, useState } from "react";
import { descripcionesDe, FormFieldContext } from "./formFieldContext";
import "./Input.css";
import "./Textarea.css";

// Como Input, pero de varias líneas: dentro de un FormField toma el id del label
// y el estado de error. Con `contador` y `maxLength` muestra los caracteres
// usados ("120/500"), útil para descripciones.
const Textarea = ({
  className = "",
  contador = false,
  maxLength,
  rows = 4,
  onChange,
  ...props
}) => {
  const campo = useContext(FormFieldContext);
  const contadorId = useId();
  // Funciona controlado (value) o no controlado (defaultValue, como lo usa useFormSubmit).
  const [largoNoControlado, setLargo] = useState(String(props.defaultValue ?? "").length);
  const largo = props.value !== undefined ? String(props.value).length : largoNoControlado;
  const conContador = contador && maxLength !== undefined;

  const describedBy = descripcionesDe(campo, conContador && contadorId);

  return (
    <div className="textarea">
      <textarea
        id={campo?.id}
        aria-invalid={campo?.invalido || undefined}
        aria-describedby={describedBy}
        className={`input-base textarea-control ${className}`.trim()}
        maxLength={maxLength}
        rows={rows}
        onChange={(evento) => {
          setLargo(evento.target.value.length);
          onChange?.(evento);
        }}
        {...props}
      />
      {conContador && (
        <span
          id={contadorId}
          className={`textarea-contador ${largo >= maxLength ? "textarea-contador-limite" : ""}`.trim()}
        >
          {largo}/{maxLength}
        </span>
      )}
    </div>
  );
};

export default Textarea;
