import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import Button from "../../../components/ui/Button";
import ConfirmDialog from "../../../components/ui/ConfirmDialog";
import Icono from "../../../components/ui/Icono";
import { ocultarEvento } from "../../../services/eventos";
import { clavesEventos } from "../clavesEventos";

// "Ocultar evento" con confirmación, para administradores (RF-05.1). Un evento
// oculto deja de verse en todos lados, también su ficha (404), así que al
// confirmar se llama a onOcultado (la ficha vuelve a la página anterior) y
// recién después se actualiza la caché: si se invalidara antes, la ficha se
// volvería a pedir y mostraría "No encontramos este evento" por un instante.
// Quien lo usa decide si mostrarlo (permisosSobre().puedeOcultar).
const BotonOcultarEvento = ({ evento, onOcultado, className }) => {
  const [abierto, setAbierto] = useState(false);
  const queryClient = useQueryClient();

  const confirmar = async () => {
    await ocultarEvento(evento.id_evento);
    onOcultado?.();
    queryClient.removeQueries({ queryKey: clavesEventos.detalle(evento.id_evento) });
    await queryClient.invalidateQueries({ queryKey: clavesEventos.todas });
  };

  return (
    <>
      <Button variant="outline" className={className} onClick={() => setAbierto(true)}>
        <Icono nombre="visibility_off" />
        Ocultar evento
      </Button>
      <ConfirmDialog
        abierto={abierto}
        onCerrar={() => setAbierto(false)}
        onConfirmar={confirmar}
        titulo="¿Ocultar el evento?"
        descripcion={`«${evento.titulo}» va a dejar de verse en el mapa, en las búsquedas y en su ficha, también para quien tenga el enlace. Su organizador lo va a seguir viendo en "Mis eventos" como oculto. No se puede deshacer.`}
        textoConfirmar="Ocultar evento"
        textoProcesando="Ocultando..."
        variante="destructive"
      />
    </>
  );
};

export default BotonOcultarEvento;
