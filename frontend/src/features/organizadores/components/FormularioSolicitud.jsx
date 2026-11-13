import FormError from "../../../components/ui/FormError";
import FormField from "../../../components/ui/FormField";
import Input from "../../../components/ui/Input";
import SubmitButton from "../../../components/ui/SubmitButton";
import Textarea from "../../../components/ui/Textarea";
import { useFormSubmit } from "../../../hooks/useFormSubmit";
import { ApiError } from "../../../services/client";
import { solicitarOrganizador } from "../../../services/organizadores";
import { useAuth } from "../../auth/context/AuthContext";
import "./FormularioSolicitud.css";

// nombre_publico es VARCHAR(255) en la base. La descripción es TEXT: el límite
// es solo del frontend, para que la solicitud sea breve.
const MAX_NOMBRE = 255;
const MAX_DESCRIPCION = 1000;

// El backend acepta textos vacíos o solo con espacios, así que se controla acá.
function validar({ nombre_publico, descripcion }) {
  const errores = {};
  if (!nombre_publico.trim()) errores.nombre_publico = "Ingresá el nombre público.";
  if (!descripcion.trim()) errores.descripcion = "Contá brevemente qué eventos organizás.";
  return errores;
}

// Formulario de la solicitud de organizador (RF-01.6). Al enviarla se vuelve a
// pedir el usuario (GET /auth/me): su organizador pasa a PENDIENTE y la página
// muestra ese estado en lugar del formulario.
// `nombreAnterior`: el de una solicitud rechazada, para no tener que reescribirlo.
const FormularioSolicitud = ({ nombreAnterior = "", onEnviada }) => {
  const { refrescarUsuario } = useAuth();

  const { submit, enviando, errores, errorGeneral } = useFormSubmit(
    async ({ nombre_publico, descripcion }) => {
      try {
        await solicitarOrganizador({
          nombre_publico: nombre_publico.trim(),
          descripcion: descripcion.trim(),
        });
      } catch (error) {
        // 409 o 403: el estado cambió en otra pestaña o lo cambió un
        // administrador. Al refrescar, la página pasa a mostrar el actual.
        if (error instanceof ApiError && [403, 409].includes(error.status)) {
          await refrescarUsuario().catch(() => {});
        }
        throw error;
      }
      onEnviada?.();
      await refrescarUsuario();
    },
    { validar },
  );

  return (
    <form className="formulario-solicitud" onSubmit={submit}>
      <FormField label="Nombre público" error={errores.nombre_publico}>
        <Input
          name="nombre_publico"
          defaultValue={nombreAnterior}
          placeholder="Ej.: Centro Cultural del Sur"
          maxLength={MAX_NOMBRE}
          autoComplete="organization"
          required
        />
      </FormField>
      <FormField label="Descripción" error={errores.descripcion}>
        <Textarea
          name="descripcion"
          placeholder="Quiénes son y qué tipo de eventos organizan."
          maxLength={MAX_DESCRIPCION}
          rows={5}
          contador
          required
        />
      </FormField>
      <FormError mensaje={errorGeneral} />
      <SubmitButton
        className="formulario-solicitud-enviar"
        enviando={enviando}
        textoEnviando="Enviando..."
      >
        Enviar solicitud
      </SubmitButton>
    </form>
  );
};

export default FormularioSolicitud;
