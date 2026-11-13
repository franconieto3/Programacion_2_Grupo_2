import { Link } from "react-router-dom";
import Badge from "../../../components/ui/Badge";
import Icono from "../../../components/ui/Icono";
import { bloqueFecha, cuando, precio } from "../formato";
import BadgeEstado from "./BadgeEstado";
import "./TarjetaEvento.css";
import "./FilaMiEvento.css";

// Un evento en "Mis eventos" (RF-02.5). Se ve como TarjetaEvento, con el
// estado del evento adelante. El título es el enlace a la ficha y su área
// cubre toda la fila; `children` son acciones (editar, cancelar) que quedan
// por encima y se pueden usar sin abrir la ficha.
// Un evento OCULTO no tiene enlace: la ficha responde 404 para todos, también
// para su organizador (es una baja por moderación).
const FilaMiEvento = ({ evento, children }) => {
  const { mes, dia } = bloqueFecha(evento.fecha_inicio);
  const { lugar } = evento;
  const textoPrecio = precio(evento.precio);
  const textoLugar = [lugar.nombre, lugar.direccion].filter(Boolean).join(" · ");
  const oculto = evento.estado === "OCULTO";

  return (
    <article className={`fila-mi-evento ${oculto ? "fila-mi-evento-oculto" : ""}`.trim()}>
      <span className="tarjeta-evento-fecha" aria-hidden="true">
        <span className="tarjeta-evento-mes">{mes}</span>
        <span className="tarjeta-evento-dia">{dia}</span>
      </span>

      <div className="tarjeta-evento-cuerpo">
        <div className="fila-mi-evento-estado">
          <BadgeEstado evento={evento} />
        </div>
        <h3 className="tarjeta-evento-titulo fila-mi-evento-titulo">
          {oculto ? (
            evento.titulo
          ) : (
            <Link to={`/eventos/${evento.id_evento}`} className="fila-mi-evento-enlace">
              {evento.titulo}
            </Link>
          )}
        </h3>
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
        {oculto && (
          <p className="fila-mi-evento-nota">
            Un administrador lo ocultó: no aparece en el mapa ni en las búsquedas.
          </p>
        )}
        {(evento.categorias.length > 0 || textoPrecio) && (
          <span className="tarjeta-evento-pie">
            {evento.categorias.map((categoria) => (
              <Badge key={categoria.slug}>{categoria.nombre}</Badge>
            ))}
            {textoPrecio && <span className="tarjeta-evento-precio">{textoPrecio}</span>}
          </span>
        )}
      </div>

      {children && <div className="fila-mi-evento-acciones">{children}</div>}
    </article>
  );
};

export default FilaMiEvento;
