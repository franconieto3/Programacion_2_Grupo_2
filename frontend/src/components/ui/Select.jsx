import { useContext } from "react";
import { descripcionesDe, FormFieldContext } from "./formFieldContext";
import Icono from "./Icono";
import "./Input.css";
import "./Select.css";

// <select> nativo con el estilo de Input (accesible y, en el celular, con el
// selector del sistema). Dentro de un FormField toma el id del label y el error.
// `placeholder` agrega una primera opción vacía que no se puede elegir; con
// `required`, el navegador no deja enviar el formulario sin elegir otra.
// Uso: <Select name="estado" placeholder="Elegí un estado"><option value="A">A</option></Select>
const Select = ({ className = "", placeholder, children, ...props }) => {
  const campo = useContext(FormFieldContext);
  const sinValorInicial = props.value === undefined && props.defaultValue === undefined;

  return (
    <div className={`select ${className}`.trim()}>
      <select
        id={campo?.id}
        aria-invalid={campo?.invalido || undefined}
        aria-describedby={descripcionesDe(campo)}
        className="input-base select-control"
        defaultValue={placeholder && sinValorInicial ? "" : undefined}
        {...props}
      >
        {placeholder && (
          <option value="" disabled>
            {placeholder}
          </option>
        )}
        {children}
      </select>
      <Icono nombre="expand_more" className="select-icono" />
    </div>
  );
};

export default Select;
