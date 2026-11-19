// Identidad de la marca: único lugar a tocar para cambiar nombre o logo.
// Los archivos viven en /public/brand y se sirven tal cual (sin pasar por Vite),
// así el favicon de index.html y <Logo /> usan la misma ruta.

export const NOMBRE_APP = "SpotOn";

// Isotipo (el pin con la "S"). Reemplazar el archivo o cambiar la ruta.
export const LOGO_ISOTIPO_SRC = "/brand/spoton-mark.svg";

// Variante del isotipo para modo oscuro (opcional): en el brand board la mitad
// navy pasa a blanco/crema sobre fondo navy. Mientras sea null se usa la clara.
export const LOGO_ISOTIPO_OSCURO_SRC = null;

// Logo completo (isotipo + "SpotOn") como imagen. Mientras sea null, <Logo />
// arma la versión completa con el isotipo y el wordmark en texto.
export const LOGO_COMPLETO_SRC = null;
