import "./FormError.css";

// Error general del formulario (el que no corresponde a un campo puntual).
const FormError = ({ mensaje }) => {
  if (!mensaje) return null;

  return (
    <p className="form-error" role="alert">
      {mensaje}
    </p>
  );
};

export default FormError;
