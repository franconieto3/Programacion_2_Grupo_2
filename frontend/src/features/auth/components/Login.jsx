import { Link, Navigate, useLocation } from "react-router-dom";
import FormError from "../../../components/ui/FormError";
import FormField from "../../../components/ui/FormField";
import Input from "../../../components/ui/Input";
import SubmitButton from "../../../components/ui/SubmitButton";
import { useFormSubmit } from "../../../hooks/useFormSubmit";
import { useAuth } from "../context/AuthContext";
import "./Login.css";

export function Login() {
  const { user, loading, login } = useAuth();
  const location = useLocation();
  // Si PrivateRoute mandó acá, después del login se vuelve a la página pedida.
  const destino = location.state?.from?.pathname ?? "/explorar";

  const { submit, enviando, errores, errorGeneral } = useFormSubmit(
    ({ email, password }) => login(email, password),
  );

  if (loading) return null;
  // Ya logueado, o recién logueado: login() actualiza user y se redirige acá.
  if (user) return <Navigate to={destino} replace />;

  return (
    <div className="login">
      <h2>Ingresar</h2>
      <form className="login-form" onSubmit={submit}>
        <FormField label="Email" error={errores.email}>
          <Input name="email" type="email" autoComplete="email" required />
        </FormField>
        <FormField label="Contraseña" error={errores.password}>
          <Input name="password" type="password" autoComplete="current-password" required />
        </FormField>
        <FormError mensaje={errorGeneral} />
        <SubmitButton enviando={enviando} textoEnviando="Ingresando...">
          Ingresar
        </SubmitButton>
      </form>
      <p className="login-pie">
        ¿No tenés cuenta? <Link to="/registro">Registrate</Link>
      </p>
    </div>
  );
}
