import { useId } from "react";
import { FormFieldContext } from "./formFieldContext";
import "./FormField.css";

// Envoltorio de un campo: label + control + mensaje de error.
// Uso: <FormField label="Email" error={errores.email}><Input name="email" /></FormField>
const FormField = ({ label, error, children, className = "" }) => {
  const id = useId();
  const errorId = `${id}-error`;

  return (
    <FormFieldContext.Provider value={{ id, errorId, invalido: Boolean(error) }}>
      <div className={`form-field ${className}`.trim()}>
        <label className="form-field-label" htmlFor={id}>
          {label}
        </label>
        {children}
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
