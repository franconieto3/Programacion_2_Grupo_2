import { useEffect, useId, useRef, useState } from "react";
import { ApiError } from "../../services/client";
import Button from "./Button";
import FormError from "./FormError";
import Spinner from "./Spinner";
import "./ConfirmDialog.css";

// Diálogo para confirmar una acción (cancelar u ocultar un evento...). Usa el
// <dialog> nativo en modo modal: el navegador bloquea el resto de la página,
// encierra el foco y lo devuelve al cerrar.
//
// - abierto / onCerrar: lo controla quien lo usa. Se cierra con "Cancelar",
//   con Escape o con un clic afuera.
// - onConfirmar: puede ser async. Mientras corre, los botones se deshabilitan;
//   si sale bien se llama a onCerrar, y si falla se muestra el error y el
//   diálogo queda abierto para reintentar.
// - variante: "destructive" pinta de rojo el botón de confirmar.
//
// Uso:
//   <ConfirmDialog abierto={abierto} onCerrar={() => setAbierto(false)}
//     titulo="¿Cancelar el evento?" descripcion="No se puede deshacer."
//     textoConfirmar="Cancelar evento" variante="destructive"
//     onConfirmar={() => cancelarEvento(id)} />
const ConfirmDialog = ({
  abierto,
  onCerrar,
  onConfirmar,
  titulo,
  descripcion,
  textoConfirmar = "Confirmar",
  textoCancelar = "Volver",
  textoProcesando = "Procesando...",
  variante = "default",
}) => {
  const dialogo = useRef(null);
  const [procesando, setProcesando] = useState(false);
  const [error, setError] = useState(null);
  const tituloId = useId();
  const descripcionId = useId();

  useEffect(() => {
    const elemento = dialogo.current;
    if (abierto && !elemento.open) elemento.showModal();
    if (!abierto && elemento.open) elemento.close();
  }, [abierto]);

  const cerrar = () => {
    if (procesando) return;
    setError(null);
    onCerrar();
  };

  const confirmar = async () => {
    setProcesando(true);
    setError(null);
    try {
      await onConfirmar();
      setProcesando(false);
      onCerrar();
    } catch (excepcion) {
      setProcesando(false);
      setError(
        excepcion instanceof ApiError
          ? excepcion.message
          : "No se pudo completar la acción. Revisá tu conexión e intentá de nuevo.",
      );
    }
  };

  return (
    <dialog
      ref={dialogo}
      className="dialogo"
      role="alertdialog"
      aria-labelledby={tituloId}
      aria-describedby={descripcion ? descripcionId : undefined}
      // Escape: se cierra a través de `abierto`, como el botón.
      onCancel={(evento) => {
        evento.preventDefault();
        cerrar();
      }}
      // Si igual lo cierra el navegador (Chrome lo fuerza con dos Escape
      // seguidos), se avisa para que `abierto` no quede en true.
      onClose={() => {
        if (abierto) {
          setError(null);
          onCerrar();
        }
      }}
      // Clic en el fondo: el target es el propio <dialog>, no su contenido.
      onClick={(evento) => {
        if (evento.target === dialogo.current) cerrar();
      }}
    >
      <div className="dialogo-contenido">
        <h2 id={tituloId} className="dialogo-titulo">
          {titulo}
        </h2>
        {descripcion && (
          <p id={descripcionId} className="dialogo-descripcion">
            {descripcion}
          </p>
        )}
        <FormError mensaje={error} />
        <div className="dialogo-acciones">
          {/* Va primero: es el que recibe el foco al abrir, la opción segura. */}
          <Button variant="outline" onClick={cerrar} disabled={procesando}>
            {textoCancelar}
          </Button>
          <Button
            variant={variante}
            onClick={confirmar}
            disabled={procesando}
            aria-busy={procesando}
          >
            {procesando && <Spinner tamano="sm" decorativo />}
            {procesando ? textoProcesando : textoConfirmar}
          </Button>
        </div>
      </div>
    </dialog>
  );
};

export default ConfirmDialog;
