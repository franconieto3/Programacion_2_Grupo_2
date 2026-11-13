import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import Button from "../../../components/ui/Button";
import ConfirmDialog from "../../../components/ui/ConfirmDialog";
import Icono from "../../../components/ui/Icono";
import { cancelarEvento } from "../../../services/eventos";
import { clavesEventos } from "../clavesEventos";

// "Cancelar evento" con confirmación (RF-02.4). Al confirmar llama a
// cancelarEvento() e invalida la caché de eventos: "Mis eventos", el mapa, la
// lista y la ficha se actualizan solos. Si el backend responde un error (p. ej.
// 409 porque el estado cambió), el diálogo lo muestra y queda abierto.
// - compacto: solo el ícono (para las filas de "Mis eventos"); el nombre del
//   evento va en el aria-label.
// Quien lo usa decide si mostrarlo (permisosSobre().puedeCancelar).
const BotonCancelarEvento = ({ evento, compacto = false, className }) => {
  const [abierto, setAbierto] = useState(false);
  const queryClient = useQueryClient();

  const confirmar = async () => {
    await cancelarEvento(evento.id_evento);
    await queryClient.invalidateQueries({ queryKey: clavesEventos.todas });
  };

  return (
    <>
      {compacto ? (
        <Button
          variant="ghost"
          size="icon"
          className={className}
          aria-label={`Cancelar «${evento.titulo}»`}
          title="Cancelar evento"
          onClick={() => setAbierto(true)}
        >
          <Icono nombre="event_busy" />
        </Button>
      ) : (
        <Button variant="outline" className={className} onClick={() => setAbierto(true)}>
          <Icono nombre="event_busy" />
          Cancelar evento
        </Button>
      )}
      <ConfirmDialog
        abierto={abierto}
        onCerrar={() => setAbierto(false)}
        onConfirmar={confirmar}
        titulo="¿Cancelar el evento?"
        descripcion={`«${evento.titulo}» va a dejar de aparecer en el mapa y en las búsquedas. Quien tenga el enlace va a ver que se canceló. No se puede deshacer.`}
        textoConfirmar="Cancelar evento"
        textoProcesando="Cancelando..."
        variante="destructive"
      />
    </>
  );
};

export default BotonCancelarEvento;
