import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import Avatar from "../../../components/ui/Avatar";
import Button from "../../../components/ui/Button";
import ConfirmDialog from "../../../components/ui/ConfirmDialog";
import FormError from "../../../components/ui/FormError";
import Icono from "../../../components/ui/Icono";
import Spinner from "../../../components/ui/Spinner";
import { ApiError } from "../../../services/client";
import {
  aprobarOrganizador,
  rechazarOrganizador,
  suspenderOrganizador,
} from "../../../services/organizadores";
import { useAuth } from "../../auth/context/AuthContext";
import { aFecha, ZONA_HORARIA } from "../../eventos/formato";
import { avatarDeOrganizador } from "../avatar";
import { clavesOrganizadores } from "../hooks/useOrganizadores";
import "./FilaOrganizador.css";

const formatoFecha = new Intl.DateTimeFormat("es-AR", {
  timeZone: ZONA_HORARIA,
  day: "numeric",
  month: "long",
  year: "numeric",
});

// Rechazar y suspender piden confirmación; aprobar no (si hiciera falta, se
// suspende después).
const CONFIRMACIONES = {
  rechazar: {
    accion: rechazarOrganizador,
    titulo: "¿Rechazar la solicitud?",
    descripcion: (nombre) =>
      `«${nombre}» no va a poder publicar eventos. Puede volver a enviar la solicitud más adelante.`,
    textoConfirmar: "Rechazar",
    textoProcesando: "Rechazando...",
    hecho: (nombre) => `Rechazaste la solicitud de «${nombre}».`,
  },
  suspender: {
    accion: suspenderOrganizador,
    titulo: "¿Suspender al organizador?",
    descripcion: (nombre) =>
      `«${nombre}» no va a poder crear ni editar eventos, ni volver a pedir el perfil. Sus eventos publicados siguen visibles: si alguno es inapropiado, ocultalo desde su ficha. No se puede deshacer.`,
    textoConfirmar: "Suspender",
    textoProcesando: "Suspendiendo...",
    hecho: (nombre) => `Suspendiste a «${nombre}».`,
  },
};

// Un perfil de organizador en la administración (RF-05.5, CU-05), con las
// acciones que permite su estado: aprobar o rechazar una solicitud PENDIENTE,
// suspender uno APROBADO. RECHAZADO y SUSPENDIDO no tienen acciones.
// onResuelto(mensaje): después de una acción que salió bien, para que la
// página lo anuncie (la fila se va de la pestaña al actualizarse la lista).
const FilaOrganizador = ({ organizador, onResuelto }) => {
  const { user, refrescarUsuario } = useAuth();
  const queryClient = useQueryClient();
  const [aprobando, setAprobando] = useState(false);
  const [error, setError] = useState(null);
  const [confirmando, setConfirmando] = useState(null); // "rechazar" | "suspender" | null
  const nombre = organizador.nombre_publico;

  const terminar = async (mensaje) => {
    // Si el administrador resolvió su propia solicitud, la barra tiene que
    // cambiar (p. ej. aparecer "Crear evento") sin volver a iniciar sesión.
    if (organizador.id_usuario === user.id) await refrescarUsuario().catch(() => {});
    onResuelto?.(mensaje);
    await queryClient.invalidateQueries({ queryKey: clavesOrganizadores.todas });
  };

  const aprobar = async () => {
    setAprobando(true);
    setError(null);
    try {
      await aprobarOrganizador(organizador.id_organizador);
      await terminar(`Aprobaste a «${nombre}»: ya puede publicar eventos.`);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "No se pudo conectar con el servidor.");
      // Un 409 es que el estado cambió (otro administrador): se actualiza la lista.
      if (e instanceof ApiError && e.status === 409) {
        queryClient.invalidateQueries({ queryKey: clavesOrganizadores.todas });
      }
    } finally {
      setAprobando(false);
    }
  };

  const confirmacion = confirmando && CONFIRMACIONES[confirmando];

  return (
    <article className="fila-organizador">
      <Avatar usuario={avatarDeOrganizador(nombre)} />
      <div className="fila-organizador-cuerpo">
        <h3 className="fila-organizador-nombre">{nombre}</h3>
        <p className="fila-organizador-fecha">
          Pidió el perfil el {formatoFecha.format(aFecha(organizador.fecha_creacion))}
        </p>
        <p className="fila-organizador-descripcion">{organizador.descripcion}</p>
        <FormError mensaje={error} />
      </div>

      {organizador.estado === "PENDIENTE" && (
        <div className="fila-organizador-acciones">
          <Button size="sm" onClick={aprobar} disabled={aprobando} aria-busy={aprobando}>
            {aprobando ? <Spinner tamano="sm" decorativo /> : <Icono nombre="check" />}
            Aprobar
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={() => setConfirmando("rechazar")}
            disabled={aprobando}
          >
            <Icono nombre="close" />
            Rechazar
          </Button>
        </div>
      )}
      {organizador.estado === "APROBADO" && (
        <div className="fila-organizador-acciones">
          <Button size="sm" variant="outline" onClick={() => setConfirmando("suspender")}>
            <Icono nombre="block" />
            Suspender
          </Button>
        </div>
      )}

      {confirmacion && (
        <ConfirmDialog
          abierto
          onCerrar={() => setConfirmando(null)}
          onConfirmar={async () => {
            await confirmacion.accion(organizador.id_organizador);
            await terminar(confirmacion.hecho(nombre));
          }}
          titulo={confirmacion.titulo}
          descripcion={confirmacion.descripcion(nombre)}
          textoConfirmar={confirmacion.textoConfirmar}
          textoProcesando={confirmacion.textoProcesando}
          variante="destructive"
        />
      )}
    </article>
  );
};

export default FilaOrganizador;
