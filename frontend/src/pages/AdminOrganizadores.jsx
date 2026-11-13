import { useId, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import Button from "../components/ui/Button";
import EmptyState from "../components/ui/EmptyState";
import Icono from "../components/ui/Icono";
import FilaOrganizador from "../features/organizadores/components/FilaOrganizador";
import { useOrganizadores } from "../features/organizadores/hooks/useOrganizadores";
import "./AdminOrganizadores.css";

// Una pestaña por estado. `param` es lo que va en la URL (?estado=aprobados).
const PESTANAS = [
  {
    estado: "PENDIENTE",
    param: "pendientes",
    texto: "Pendientes",
    vacio: {
      icono: "inbox",
      titulo: "No hay solicitudes pendientes",
      descripcion: "Cuando alguien pida ser organizador, la vas a ver acá.",
    },
  },
  {
    estado: "APROBADO",
    param: "aprobados",
    texto: "Aprobados",
    vacio: { icono: "storefront", titulo: "No hay organizadores aprobados" },
  },
  {
    estado: "RECHAZADO",
    param: "rechazados",
    texto: "Rechazados",
    vacio: { icono: "do_not_disturb_on", titulo: "No hay solicitudes rechazadas" },
  },
  {
    estado: "SUSPENDIDO",
    param: "suspendidos",
    texto: "Suspendidos",
    vacio: { icono: "block", titulo: "No hay organizadores suspendidos" },
  },
];

// Administración de organizadores (RF-05.5, CU-05): solicitudes pendientes
// para aprobar o rechazar, y organizadores aprobados para suspender. Solo
// administradores (AdminRoute). La pestaña queda en la URL, así sobrevive a
// una recarga.
const AdminOrganizadores = () => {
  const [params, setParams] = useSearchParams();
  const actual = PESTANAS.find((p) => p.param === params.get("estado")) ?? PESTANAS[0];
  const [aviso, setAviso] = useState(null);
  const id = useId();
  const pendientes = useOrganizadores("PENDIENTE");
  const botones = useRef([]);

  const elegir = (pestana, { foco = false } = {}) => {
    setAviso(null);
    setParams(pestana === PESTANAS[0] ? {} : { estado: pestana.param }, { replace: true });
    if (foco) botones.current[PESTANAS.indexOf(pestana)]?.focus();
  };

  // Patrón "tabs" de ARIA: flechas para moverse entre pestañas, Inicio y Fin.
  const alPresionar = (evento) => {
    const indice = PESTANAS.indexOf(actual);
    const destino = {
      ArrowRight: (indice + 1) % PESTANAS.length,
      ArrowLeft: (indice - 1 + PESTANAS.length) % PESTANAS.length,
      Home: 0,
      End: PESTANAS.length - 1,
    }[evento.key];
    if (destino === undefined) return;
    evento.preventDefault();
    elegir(PESTANAS[destino], { foco: true });
  };

  return (
    <div className="pagina">
      <h1 className="pagina-titulo">Organizadores</h1>

      <div className="admin-pestanas" role="tablist" aria-label="Estado" onKeyDown={alPresionar}>
        {PESTANAS.map((pestana, indice) => {
          const activa = pestana === actual;
          const cantidad = pestana.estado === "PENDIENTE" ? pendientes.data?.length : undefined;
          return (
            <button
              key={pestana.estado}
              ref={(elemento) => (botones.current[indice] = elemento)}
              type="button"
              role="tab"
              id={`${id}-tab-${pestana.param}`}
              aria-selected={activa}
              aria-controls={`${id}-panel`}
              tabIndex={activa ? 0 : -1}
              className={`admin-pestana ${activa ? "admin-pestana-activa" : ""}`.trim()}
              onClick={() => elegir(pestana)}
            >
              {pestana.texto}
              {cantidad > 0 && <span className="admin-pestana-cantidad">{cantidad}</span>}
            </button>
          );
        })}
      </div>

      <div
        id={`${id}-panel`}
        role="tabpanel"
        aria-labelledby={`${id}-tab-${actual.param}`}
        className="admin-panel"
      >
        <p className="admin-aviso" role="status" hidden={!aviso}>
          <Icono nombre="check_circle" />
          {aviso}
        </p>
        <ListaPorEstado key={actual.estado} pestana={actual} onResuelto={setAviso} />
      </div>
    </div>
  );
};

const ListaPorEstado = ({ pestana, onResuelto }) => {
  const { data: organizadores, isPending, error, refetch } = useOrganizadores(pestana.estado);

  if (isPending) return <EsqueletoLista />;
  if (error) {
    return (
      <EmptyState icono="cloud_off" titulo="No pudimos cargar la lista" descripcion={error.message}>
        <Button variant="outline" onClick={() => refetch()}>
          Reintentar
        </Button>
      </EmptyState>
    );
  }
  if (organizadores.length === 0) return <EmptyState {...pestana.vacio} />;

  return (
    <ul className="admin-lista">
      {organizadores.map((organizador) => (
        <li key={organizador.id_organizador}>
          <FilaOrganizador organizador={organizador} onResuelto={onResuelto} />
        </li>
      ))}
    </ul>
  );
};

const EsqueletoLista = () => (
  <ul className="admin-lista" role="status" aria-label="Cargando">
    {[60, 45, 70].map((ancho, i) => (
      <li key={i} className="admin-esqueleto" aria-hidden="true">
        <span className="esqueleto admin-esqueleto-avatar" />
        <span className="admin-esqueleto-cuerpo">
          <span className="esqueleto" style={{ width: `${ancho}%`, height: "1rem" }} />
          <span className="esqueleto" style={{ width: "30%" }} />
          <span className="esqueleto" style={{ width: "90%" }} />
        </span>
      </li>
    ))}
  </ul>
);

export default AdminOrganizadores;
