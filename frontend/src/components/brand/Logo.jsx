import {
  LOGO_COMPLETO_SRC,
  LOGO_ISOTIPO_OSCURO_SRC,
  LOGO_ISOTIPO_SRC,
  NOMBRE_APP,
} from "./marca";
import "./Logo.css";

/**
 * Logo de SpotOn.
 * - variant="full": isotipo + wordmark "Spot·On" (o la imagen LOGO_COMPLETO_SRC).
 * - variant="mark": solo el isotipo (barra colapsada, app icon, favicon).
 * `size` es el alto del isotipo en px; el wordmark escala con él.
 * `textoClassName` permite ocultar el wordmark por CSS (p. ej. en la barra
 * colapsada) sin sacarlo del DOM para lectores de pantalla.
 */
const Logo = ({ variant = "full", size = 32, className = "", textoClassName = "" }) => {
  const clases = ["logo", `logo-${variant}`, className].filter(Boolean).join(" ");

  if (variant === "full" && LOGO_COMPLETO_SRC) {
    return (
      <span className={clases} style={{ "--logo-alto": `${size}px` }}>
        <img className="logo-imagen" src={LOGO_COMPLETO_SRC} alt={NOMBRE_APP} />
      </span>
    );
  }

  return (
    <span className={clases} style={{ "--logo-alto": `${size}px` }}>
      <picture>
        {LOGO_ISOTIPO_OSCURO_SRC && (
          <source media="(prefers-color-scheme: dark)" srcSet={LOGO_ISOTIPO_OSCURO_SRC} />
        )}
        <img
          className="logo-isotipo"
          src={LOGO_ISOTIPO_SRC}
          alt={variant === "mark" ? NOMBRE_APP : ""}
          aria-hidden={variant === "mark" ? undefined : true}
        />
      </picture>
      {variant === "full" && (
        <span className={`logo-texto ${textoClassName}`.trim()}>
          Spot<span className="logo-texto-acento">On</span>
        </span>
      )}
    </span>
  );
};

export default Logo;
