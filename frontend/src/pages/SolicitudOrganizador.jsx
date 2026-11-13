import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import EmptyState from "../components/ui/EmptyState";
import Icono from "../components/ui/Icono";
import { useAuth } from "../features/auth/context/AuthContext";
import FormularioSolicitud from "../features/organizadores/components/FormularioSolicitud";
import "./SolicitudOrganizador.css";

const CLASES_BOTON = "btn-base btn-variant-default btn-size-default";
const CLASES_BOTON_OUTLINE = "btn-base btn-variant-outline btn-size-default";

// Solicitud de perfil de organizador (RF-01.6, CU-04). Lo que se muestra
// depende del estado del organizador del usuario (GET /auth/me):
// - sin perfil o RECHAZADO: el formulario (un rechazado puede volver a pedirlo);
// - PENDIENTE: que la solicitud está en revisión;
// - SUSPENDIDO: que no puede volver a pedirlo;
// - APROBADO: que ya es organizador. La barra no ofrece esta página en ese
//   caso, pero se puede llegar escribiendo la URL.
const SolicitudOrganizador = () => {
  const { user, refrescarUsuario } = useAuth();
  const { organizador } = user;
  const estado = organizador?.estado;
  // Para decir "enviada" en vez de "en revisión" justo después de enviarla.
  const [recienEnviada, setRecienEnviada] = useState(false);

  // Con la solicitud pendiente, al entrar se vuelve a pedir el usuario: si un
  // administrador la resolvió, se ve sin tener que recargar la página. Se usa
  // el estado con el que se entró (no cambia), así no se repite al enviarla.
  const [estadoAlEntrar] = useState(estado);
  useEffect(() => {
    if (estadoAlEntrar === "PENDIENTE") refrescarUsuario().catch(() => {});
  }, [estadoAlEntrar, refrescarUsuario]);

  let contenido;
  if (estado === "APROBADO") {
    contenido = (
      <EmptyState
        icono="verified"
        titulo="Ya sos organizador"
        descripcion={`Publicás eventos como «${organizador.nombre_publico}».`}
      >
        <div className="solicitud-acciones">
          <Link to="/eventos/nuevo" className={CLASES_BOTON}>
            Crear evento
          </Link>
          <Link to="/mis-eventos" className={CLASES_BOTON_OUTLINE}>
            Mis eventos
          </Link>
        </div>
      </EmptyState>
    );
  } else if (estado === "PENDIENTE") {
    contenido = (
      <EmptyState
        icono={recienEnviada ? "mark_email_read" : "hourglass_top"}
        titulo={recienEnviada ? "Enviamos tu solicitud" : "Tu solicitud está en revisión"}
        descripcion={`Pediste publicar como «${organizador.nombre_publico}». Cuando un administrador la apruebe, vas a ver «Crear evento» en la barra de navegación.`}
      >
        <Link to="/explorar" className={CLASES_BOTON_OUTLINE}>
          Volver a Explorar
        </Link>
      </EmptyState>
    );
  } else if (estado === "SUSPENDIDO") {
    contenido = (
      <EmptyState
        icono="block"
        titulo="Tu perfil de organizador está suspendido"
        descripcion="No podés publicar eventos ni volver a solicitar el perfil. Si creés que es un error, escribile al equipo de la plataforma."
      />
    );
  } else {
    contenido = (
      <>
        <p className="solicitud-intro">
          Con un perfil de organizador podés publicar tus eventos en el mapa. Un
          administrador revisa cada solicitud antes de aprobarla.
        </p>
        {estado === "RECHAZADO" && (
          <p className="solicitud-aviso" role="status">
            <Icono nombre="info" />
            Tu solicitud anterior no fue aprobada. Podés revisar los datos y
            enviarla de nuevo.
          </p>
        )}
        <FormularioSolicitud
          nombreAnterior={organizador?.nombre_publico}
          onEnviada={() => setRecienEnviada(true)}
        />
      </>
    );
  }

  return (
    <div className="pagina solicitud">
      <h1 className="pagina-titulo">Ser organizador</h1>
      {contenido}
    </div>
  );
};

export default SolicitudOrganizador;
