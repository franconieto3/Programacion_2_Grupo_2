import { Link, Navigate, useNavigate } from "react-router-dom";
import FormError from "../../../components/ui/FormError";
import FormField from "../../../components/ui/FormField";
import Input from "../../../components/ui/Input";
import SubmitButton from "../../../components/ui/SubmitButton";
import { useFormSubmit } from "../../../hooks/useFormSubmit";
import { registrar } from "../../../services/auth";
import { useAuth } from "../context/AuthContext";
import "./Auth.css";

// Validaciones que el navegador no hace solo con required/minLength.
function validar({ nombre, apellido, password, password_confirmacion }) {
  const errores = {};
  // El backend acepta "   " (min_length cuenta los espacios), así que se controla acá.
  if (!nombre.trim()) errores.nombre = "Ingresá tu nombre.";
  if (!apellido.trim()) errores.apellido = "Ingresá tu apellido.";
  if (password !== password_confirmacion) {
    errores.password_confirmacion = "Las contraseñas no coinciden.";
  }
  return errores;
}

export function Registro() {
  const { user, loading, login } = useAuth();
  const navigate = useNavigate();

  const { submit, enviando, errores, errorGeneral } = useFormSubmit(
    async ({ email, password, nombre, apellido }) => {
      // La confirmación de la contraseña no se envía: solo existe en el frontend.
      await registrar({ email, password, nombre: nombre.trim(), apellido: apellido.trim() });
      // El backend no inicia sesión al registrar, así que se hace acá.
      try {
        await login(email, password);
      } catch {
        // La cuenta ya existe: no tiene sentido mostrar un error en este formulario.
        navigate("/ingresar", {
          replace: true,
          state: { aviso: "Tu cuenta se creó. Iniciá sesión para continuar.", email },
        });
      }
    },
    { validar },
  );

  if (loading) return null;
  // Ya logueado, o recién registrado y logueado: login() actualiza user y se redirige acá.
  if (user) return <Navigate to="/explorar" replace />;

  return (
    <div className="auth">
      <h2>Crear cuenta</h2>
      <form className="auth-form" onSubmit={submit}>
        <div className="auth-fila">
          <FormField label="Nombre" error={errores.nombre}>
            <Input name="nombre" autoComplete="given-name" maxLength={255} required />
          </FormField>
          <FormField label="Apellido" error={errores.apellido}>
            <Input name="apellido" autoComplete="family-name" maxLength={255} required />
          </FormField>
        </div>
        <FormField label="Email" error={errores.email}>
          <Input name="email" type="email" autoComplete="email" required />
        </FormField>
        <FormField label="Contraseña" error={errores.password}>
          <Input
            name="password"
            type="password"
            autoComplete="new-password"
            minLength={8}
            maxLength={128}
            required
          />
        </FormField>
        <FormField label="Repetir contraseña" error={errores.password_confirmacion}>
          <Input name="password_confirmacion" type="password" autoComplete="new-password" required />
        </FormField>
        <FormError mensaje={errorGeneral} />
        <SubmitButton className="auth-submit" enviando={enviando} textoEnviando="Creando cuenta...">
          Crear cuenta
        </SubmitButton>
      </form>
      <p className="auth-pie">
        ¿Ya tenés cuenta? <Link to="/ingresar">Iniciá sesión</Link>
      </p>
    </div>
  );
}
