import { createContext } from "react";

// FormField comparte con su control (Input, y a futuro Select, Textarea...) el id
// del label y el estado de error, así no hay que pasarlos a mano en cada campo.
export const FormFieldContext = createContext(null);
