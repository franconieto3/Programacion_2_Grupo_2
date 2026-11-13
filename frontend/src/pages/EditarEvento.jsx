import { useQueryClient } from "@tanstack/react-query";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";
import Button from "../components/ui/Button";
import EmptyState from "../components/ui/EmptyState";
import Spinner from "../components/ui/Spinner";
import { useAuth } from "../features/auth/context/AuthContext";
import { cambiosEntre } from "../features/eventos/cambiosEvento";
import { clavesEventos } from "../features/eventos/clavesEventos";
import FormularioEvento from "../features/eventos/components/FormularioEvento";
import { useEvento } from "../features/eventos/hooks/useEvento";
import { permisosSobre } from "../features/eventos/permisos";
import { editarEvento } from "../services/eventos";

const CLASES_BOTON = "btn-base btn-variant-outline btn-size-default";

const NO_EDITABLE = {
  CANCELADO: "Este evento está cancelado y ya no se puede editar.",
  OCULTO: "Este evento lo ocultó un administrador y ya no se puede editar.",
};

// Edición de un evento propio (RF-02.4), con el mismo FormularioEvento del
// alta. Manda en el PATCH solo los campos que cambiaron; si no cambió nada,
// vuelve a la ficha sin llamar a la API. Va dentro de OrganizadorRoute; que el
// evento sea suyo y se pueda editar se controla acá (el backend igual responde
// 403 o 409).
const EditarEvento = () => {
  const { idEvento } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const queryClient = useQueryClient();
  const { data: evento, isPending, error, noEncontrado, refetch } = useEvento(idEvento);

  const irAFicha = (aviso) =>
    navigate(`/eventos/${idEvento}`, { replace: true, state: aviso ? { aviso } : undefined });

  const guardar = async (datos) => {
    const cambios = cambiosEntre(evento, datos);
    if (Object.keys(cambios).length === 0) return irAFicha("No había cambios para guardar.");
    await editarEvento(idEvento, cambios);
    await queryClient.invalidateQueries({ queryKey: clavesEventos.todas });
    irAFicha("Guardaste los cambios.");
  };

  const descartar = () => (location.key !== "default" ? navigate(-1) : irAFicha());

  let contenido;
  if (noEncontrado) {
    contenido = (
      <EmptyState
        icono="event_busy"
        titulo="No encontramos este evento"
        descripcion="Puede que el enlace esté mal escrito o que el evento ya no esté disponible."
      >
        <Link to="/mis-eventos" className={CLASES_BOTON}>
          Ir a Mis eventos
        </Link>
      </EmptyState>
    );
  } else if (error) {
    contenido = (
      <EmptyState icono="cloud_off" titulo="No pudimos cargar el evento" descripcion={error.message}>
        <Button variant="outline" onClick={() => refetch()}>
          Reintentar
        </Button>
      </EmptyState>
    );
  } else if (isPending) {
    contenido = <Spinner etiqueta="Cargando el evento" />;
  } else {
    const { esPropio, puedeEditar } = permisosSobre(evento, user);
    if (!puedeEditar) {
      contenido = (
        <EmptyState
          icono="edit_off"
          titulo="No podés editar este evento"
          descripcion={
            esPropio
              ? NO_EDITABLE[evento.estado]
              : "Solo el organizador que lo publicó puede editarlo."
          }
        >
          <Link to={`/eventos/${idEvento}`} className={CLASES_BOTON}>
            Ver el evento
          </Link>
        </EmptyState>
      );
    } else {
      contenido = (
        <FormularioEvento
          // Con otra clave, el formulario arranca de nuevo con los datos del evento.
          key={evento.id_evento}
          inicial={evento}
          onEnviar={guardar}
          textoEnviar="Guardar cambios"
          textoEnviando="Guardando..."
        >
          <Button type="button" variant="ghost" onClick={descartar}>
            Descartar
          </Button>
        </FormularioEvento>
      );
    }
  }

  return (
    <div className="pagina">
      <h1 className="pagina-titulo">Editar evento</h1>
      {contenido}
    </div>
  );
};

export default EditarEvento;
