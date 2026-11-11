import Button from "./Button";

// Botón de envío que se deshabilita mientras el formulario se está enviando,
// para evitar dobles envíos.
const SubmitButton = ({
  enviando = false,
  textoEnviando = "Enviando...",
  disabled,
  children,
  ...props
}) => (
  <Button type="submit" disabled={enviando || disabled} aria-busy={enviando} {...props}>
    {enviando ? textoEnviando : children}
  </Button>
);

export default SubmitButton;
