import { useContext } from "react";
import { FormFieldContext } from "./formFieldContext";
import "./Input.css";

// Dentro de un FormField toma de ahí el id (para el label) y el estado de error;
// fuera de uno funciona como un <input> común.
const Input = ({ className = "", ...props }) => {
  const campo = useContext(FormFieldContext);

  return (
    <input
      id={campo?.id}
      aria-invalid={campo?.invalido || undefined}
      aria-describedby={campo?.invalido ? campo.errorId : undefined}
      className={`input-base ${className}`.trim()}
      {...props}
    />
  );
};

export default Input;
