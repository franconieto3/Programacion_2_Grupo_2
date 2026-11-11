import { useState } from "react";
import Input from "./Input";
import "./PasswordInput.css";

// Input de contraseña con un botón para mostrarla u ocultarla. Usa Input por
// dentro, así que dentro de un FormField queda conectado al label y al error.
const PasswordInput = (props) => {
  const [visible, setVisible] = useState(false);

  return (
    <div className="password-input">
      <Input {...props} type={visible ? "text" : "password"} />
      <button
        type="button"
        className="password-input-toggle"
        onClick={() => setVisible((v) => !v)}
        aria-label={visible ? "Ocultar contraseña" : "Mostrar contraseña"}
        aria-pressed={visible}
      >
        {/* El ícono muestra la acción: ojo abierto para mostrar, tachado para ocultar. */}
        <i className="material-icons" aria-hidden="true">
          {visible ? "visibility_off" : "visibility"}
        </i>
      </button>
    </div>
  );
};

export default PasswordInput;
