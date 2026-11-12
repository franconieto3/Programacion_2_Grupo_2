import { Link } from "react-router-dom";
import Badge from "../../../components/ui/Badge";
import Icono from "../../../components/ui/Icono";
import { bloqueFecha, cuando, precio } from "../formato";
import "./TarjetaEvento.css";

// Un evento en la lista del descubrimiento (RF-03.2). Toda la tarjeta es un
// enlace a la ficha de detalle.
const TarjetaEvento = ({ evento }) => {
  const { mes, dia } = bloqueFecha(evento.fecha_inicio);
  const { lugar } = evento;
  const textoPrecio = precio(evento.precio);
  const textoLugar = [lugar.nombre, lugar.direccion].filter(Boolean).join(" · ");

  return (
    <Link to={`/eventos/${evento.id_evento}`} className="tarjeta-evento">
      <span className="tarjeta-evento-fecha" aria-hidden="true">
        <span className="tarjeta-evento-mes">{mes}</span>
        <span className="tarjeta-evento-dia">{dia}</span>
      </span>

      <span className="tarjeta-evento-cuerpo">
        <span className="tarjeta-evento-titulo">{evento.titulo}</span>
        <span className="tarjeta-evento-dato">
          <Icono nombre="schedule" />
          {cuando(evento)}
        </span>
        {textoLugar && (
          <span className="tarjeta-evento-dato">
            <Icono nombre="location_on" />
            <span className="tarjeta-evento-lugar">{textoLugar}</span>
          </span>
        )}
        {(evento.categorias.length > 0 || textoPrecio) && (
          <span className="tarjeta-evento-pie">
            {evento.categorias.map((categoria) => (
              <Badge key={categoria.slug}>{categoria.nombre}</Badge>
            ))}
            {textoPrecio && <span className="tarjeta-evento-precio">{textoPrecio}</span>}
          </span>
        )}
      </span>
    </Link>
  );
};

export default TarjetaEvento;
