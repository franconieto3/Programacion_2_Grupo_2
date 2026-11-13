import Badge from "../../../components/ui/Badge";
import { yaTermino } from "../formato";

const ESTADOS = {
  BORRADOR: { texto: "Borrador", variante: "advertencia", icono: "edit_note" },
  PUBLICADO: { texto: "Publicado", variante: "exito", icono: "public" },
  CANCELADO: { texto: "Cancelado", variante: "error", icono: "event_busy" },
  OCULTO: { texto: "Oculto", variante: "error", icono: "visibility_off" },
};
const FINALIZADO = { texto: "Finalizado", variante: "neutral", icono: "history" };

// Estado de un evento para su organizador (RF-02.5): borrador, publicado,
// cancelado u oculto por un administrador. Un publicado que ya terminó se
// muestra como "Finalizado": sigue PUBLICADO en la API, pero ya no aparece en
// las búsquedas.
const BadgeEstado = ({ evento, className }) => {
  const estado =
    evento.estado === "PUBLICADO" && yaTermino(evento) ? FINALIZADO : ESTADOS[evento.estado];
  if (!estado) return null;

  return (
    <Badge variante={estado.variante} icono={estado.icono} className={className}>
      {estado.texto}
    </Badge>
  );
};

export default BadgeEstado;
