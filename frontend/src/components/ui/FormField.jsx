import { useId } from "react";
import { FormFieldContext } from "./formFieldContext";
import "./FormField.css";

// Envoltorio de un campo: label + control + ayuda opcional + mensaje de error.
// Uso: <FormField label="Email" error={errores.email}><Input name="email" /></FormField>
// `ayuda`: texto chico bajo el control (p. ej. "Dejalo vacío si no tiene
// precio"); el control lo enlaza con aria-describedby.
const FormField = ({ label, error, ayuda, children, className = "" }) => {
  const id = useId();
  const errorId = `${id}-error`;
  const ayudaId = ayuda ? `${id}-ayuda` : undefined;

  return (
    <FormFieldContext.Provider value={{ id, errorId, ayudaId, invalido: Boolean(error) }}>
      <div className={`form-field ${className}`.trim()}>
        <label className="form-field-label" htmlFor={id}>
          {label}
        </label>
        {children}
        {ayuda && (
          <p id={ayudaId} className="form-field-ayuda">
            {ayuda}
          </p>
        )}
        {error && (
          <p id={errorId} className="form-field-error">
            {error}
          </p>
        )}
      </div>
    </FormFieldContext.Provider>
  );
};

export default FormField;
