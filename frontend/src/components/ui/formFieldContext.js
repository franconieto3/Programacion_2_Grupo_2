import { createContext } from "react";

// FormField comparte con su control (Input, Select, Textarea) el id del label,
// el estado de error y el id del texto de ayuda, así no hay que pasarlos a
// mano en cada campo.
export const FormFieldContext = createContext(null);

// aria-describedby de un control dentro de un FormField: la ayuda, el error
// (si hay) y los ids extra que pase el control (p. ej. el contador de Textarea).
export function descripcionesDe(campo, ...extra) {
  const ids = [campo?.ayudaId, campo?.invalido && campo.errorId, ...extra].filter(Boolean);
  return ids.length > 0 ? ids.join(" ") : undefined;
}
