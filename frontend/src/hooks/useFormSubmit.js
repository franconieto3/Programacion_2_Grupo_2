import { useState } from "react";
import { ApiError } from "../services/client";

// Separa un error del backend en errores por campo y un error general.
// En los 422 de validación, FastAPI indica el campo en loc: ['body', 'email'].
// Los que no apuntan a un campo (loc: ['body'], p. ej. validaciones entre dos
// campos) y el resto de los errores (401, 409...) van al error general.
function interpretarError(error) {
  if (!(error instanceof ApiError)) {
    return { campos: {}, general: "No se pudo conectar con el servidor." };
  }
  if (error.status !== 422 || !Array.isArray(error.detalle)) {
    return { campos: {}, general: error.message };
  }

  const campos = {};
  const generales = [];
  for (const { loc = [], msg } of error.detalle) {
    // Pydantic antepone "Value error, " a los mensajes de los validadores propios.
    const mensaje = msg.replace(/^Value error, /, "");
    const campo = loc[0] === "body" ? loc[1] : undefined;
    if (campo !== undefined) campos[campo] ??= mensaje;
    else generales.push(mensaje);
  }
  return { campos, general: generales.join(" ") || null };
}

// Maneja el envío de un formulario: arma un objeto con los valores (por el
// atributo name de cada campo), llama a `accion` y expone el estado del envío.
// Uso: const { submit, enviando, errores, errorGeneral } = useFormSubmit(accion)
//      <form onSubmit={submit}>
export function useFormSubmit(accion) {
  const [enviando, setEnviando] = useState(false);
  const [errores, setErrores] = useState({});
  const [errorGeneral, setErrorGeneral] = useState(null);

  const submit = async (evento) => {
    evento.preventDefault();
    if (enviando) return;
    const datos = Object.fromEntries(new FormData(evento.currentTarget));

    setEnviando(true);
    setErrores({});
    setErrorGeneral(null);
    try {
      return await accion(datos);
    } catch (error) {
      const { campos, general } = interpretarError(error);
      setErrores(campos);
      setErrorGeneral(general);
    } finally {
      setEnviando(false);
    }
  };

  return { submit, enviando, errores, errorGeneral };
}
