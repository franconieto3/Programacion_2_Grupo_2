import Badge from "../../../components/ui/Badge";

// RF-05.2: distingue los eventos que cargó el equipo de la plataforma (seed)
// de los publicados por organizadores. No muestra nada en los demás.
const BadgeEquipo = ({ evento }) =>
  evento.origen === "SEED_EQUIPO" ? (
    <Badge variante="info" icono="verified">
      Equipo de la plataforma
    </Badge>
  ) : null;

export default BadgeEquipo;
