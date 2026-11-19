import { Link, Navigate, useLocation } from "react-router-dom";
import FormError from "../../../components/ui/FormError";
import FormField from "../../../components/ui/FormField";
import Input from "../../../components/ui/Input";
import PasswordInput from "../../../components/ui/PasswordInput";
import SubmitButton from "../../../components/ui/SubmitButton";
import { useFormSubmit } from "../../../hooks/useFormSubmit";
import { useAuth } from "../context/AuthContext";
import Logo from "../../../components/brand/Logo";
import Pie from "../../../components/brand/Pie";
import "./Auth.css";

export function Login() {
  const { user, loading, login } = useAuth();
  const location = useLocation();
  // Si PrivateRoute mandó acá, después del login se vuelve a la página pedida.
  const destino = location.state?.from?.pathname ?? "/explorar";
  // Registro manda acá un aviso y el email si creó la cuenta pero no pudo iniciar sesión.
  const aviso = location.state?.aviso;
  const { submit, enviando, errores, errorGeneral } = useFormSubmit(
    ({ email, password }) => login(email, password),
  );

  if (loading) return null;
  // Ya logueado, o recién logueado: login() actualiza user y se redirige acá.
  if (user) return <Navigate to={destino} replace />;

  return (
    <div className="auth-pantalla">
      <div className="auth">
        <Logo size={44} className="auth-logo" />
        <div className="auth-tarjeta">
          <h2 className="auth-titulo">Iniciar sesión</h2>
          <p className="auth-subtitulo">Encontrá los eventos que pasan cerca tuyo.</p>
          {aviso && (
            <p className="auth-aviso" role="status">
              {aviso}
            </p>
          )}
          <form className="auth-form" onSubmit={submit}>
            <FormField label="Email" error={errores.email}>
              <Input
                name="email"
                type="email"
                autoComplete="email"
                defaultValue={location.state?.email}
                required
              />
            </FormField>
            <FormField label="Contraseña" error={errores.password}>
              <PasswordInput name="password" autoComplete="current-password" required />
            </FormField>
            <FormError mensaje={errorGeneral} />
            <SubmitButton
              variant="brand"
              size="lg"
              className="auth-submit"
              enviando={enviando}
              textoEnviando="Ingresando..."
            >
              Ingresar
            </SubmitButton>
          </form>
        </div>
        <p className="auth-pie">
          ¿No tenés cuenta? <Link to="/registro">Registrate</Link>
        </p>
      </div>
      <Pie className="auth-footer" />
    </div>
  );
}
