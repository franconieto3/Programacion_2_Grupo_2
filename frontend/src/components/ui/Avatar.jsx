import "./Avatar.css";

// Iniciales del usuario en un círculo. No hay fotos de perfil todavía.
function iniciales({ nombre, apellido, email } = {}) {
  const letras = [nombre, apellido]
    .filter(Boolean)
    .map((parte) => parte.trim()[0])
    .join("");
  return (letras || email?.[0] || "?").toUpperCase();
}

// tamano: "sm" (24px, barra de navegación), "md" (40px) o "lg" (80px, perfil).
const Avatar = ({ usuario, tamano = "md", className = "" }) => (
  <span className={`avatar avatar-${tamano} ${className}`.trim()} aria-hidden="true">
    {iniciales(usuario)}
  </span>
);

export default Avatar;
