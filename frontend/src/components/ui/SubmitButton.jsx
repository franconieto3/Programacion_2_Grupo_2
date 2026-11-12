import Button from "./Button";
import Spinner from "./Spinner";

// Botón de envío que se deshabilita mientras el formulario se está enviando,
// para evitar dobles envíos. Mientras tanto muestra un spinner (decorativo:
// aria-busy ya avisa que está ocupado).
const SubmitButton = ({
  enviando = false,
  textoEnviando = "Enviando...",
  disabled,
  children,
  ...props
}) => (
  <Button type="submit" disabled={enviando || disabled} aria-busy={enviando} {...props}>
    {enviando ? (
      <>
        <Spinner tamano="sm" decorativo />
        {textoEnviando}
      </>
    ) : (
      children
    )}
  </Button>
);

export default SubmitButton;
