import { createContext, useContext } from "react";

// Ranura en el centro de la barra superior. Layout guarda acá el nodo DOM y
// una página puede renderizar ahí su propio contenido con createPortal (p. ej.
// Explorar pone su buscador de lugares, que mueve el mapa de la página).
// Vale null mientras la barra no está montada o fuera del layout.
export const RanuraBarraContext = createContext(null);

export const useRanuraBarra = () => useContext(RanuraBarraContext);
