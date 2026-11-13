import { useState } from "react";
import Badge from "../components/ui/Badge";
import Button from "../components/ui/Button";
import ConfirmDialog from "../components/ui/ConfirmDialog";
import EmptyState from "../components/ui/EmptyState";
import FormField from "../components/ui/FormField";
import Input from "../components/ui/Input";
import Select from "../components/ui/Select";
import Spinner from "../components/ui/Spinner";
import SubmitButton from "../components/ui/SubmitButton";
import Textarea from "../components/ui/Textarea";
import SelectorUbicacion from "../features/ubicacion/components/SelectorUbicacion";
import { ApiError } from "../services/client";
import "./CatalogoComponentes.css";

// Catálogo de los componentes de components/ui (y de alguno de features/ que
// conviene probar suelto, como SelectorUbicacion), solo en desarrollo
// (/dev/componentes, ver App.jsx). Sirve para revisar el diseño en claro y
// oscuro sin tener que llegar a la pantalla donde se usa cada uno.

const esperar = (ms) => new Promise((resolver) => setTimeout(resolver, ms));

const Seccion = ({ titulo, children }) => (
  <section className="catalogo-seccion">
    <h2 className="catalogo-seccion-titulo">{titulo}</h2>
    {children}
  </section>
);

const CatalogoComponentes = () => {
  const [dialogo, setDialogo] = useState(null); // "ok" | "falla" | null
  const [punto, setPunto] = useState(null);
  const [lugarBuscado, setLugarBuscado] = useState(null);
  const [errorUbicacion, setErrorUbicacion] = useState(false);

  return (
    <div className="pagina catalogo">
      <h1 className="pagina-titulo">Componentes</h1>

      <Seccion titulo="Button">
        <div className="catalogo-fila">
          <Button>Default</Button>
          <Button variant="secondary">Secondary</Button>
          <Button variant="outline">Outline</Button>
          <Button variant="ghost">Ghost</Button>
          <Button variant="destructive">Destructive</Button>
          <Button disabled>Deshabilitado</Button>
          <SubmitButton enviando textoEnviando="Guardando...">
            Guardar
          </SubmitButton>
        </div>
      </Seccion>

      <Seccion titulo="Badge">
        <div className="catalogo-fila">
          <Badge>Borrador</Badge>
          <Badge variante="exito">Publicado</Badge>
          <Badge variante="advertencia">Pendiente</Badge>
          <Badge variante="error">Cancelado</Badge>
          <Badge variante="info" icono="verified">
            Equipo de la plataforma
          </Badge>
          <Badge icono="music_note">Música</Badge>
        </div>
      </Seccion>

      <Seccion titulo="Campos">
        <div className="catalogo-campos">
          <FormField label="Input">
            <Input placeholder="Nombre del evento" />
          </FormField>
          <FormField label="Select">
            <Select placeholder="Elegí una categoría">
              <option value="musica">Música</option>
              <option value="teatro">Teatro</option>
              <option value="gastronomia">Gastronomía</option>
            </Select>
          </FormField>
          <FormField label="Textarea con contador">
            <Textarea
              placeholder="Contá de qué se trata"
              maxLength={200}
              contador
              defaultValue="Música en vivo todos los viernes."
            />
          </FormField>
          <FormField label="Con error" error="Este campo es obligatorio.">
            <Select placeholder="Elegí un estado">
              <option value="A">A</option>
            </Select>
          </FormField>
        </div>
      </Seccion>

      <Seccion titulo="Spinner">
        <div className="catalogo-fila">
          <Spinner tamano="sm" />
          <Spinner />
          <Spinner tamano="lg" />
        </div>
      </Seccion>

      <Seccion titulo="EmptyState">
        <EmptyState
          icono="event_busy"
          titulo="Todavía no publicaste eventos"
          descripcion="Cuando publiques uno, lo vas a ver acá con su estado."
        >
          <Button>Crear evento</Button>
        </EmptyState>
      </Seccion>

      <Seccion titulo="ConfirmDialog">
        <div className="catalogo-fila">
          <Button variant="destructive" onClick={() => setDialogo("ok")}>
            Cancelar evento
          </Button>
          <Button variant="outline" onClick={() => setDialogo("falla")}>
            Confirmación que falla
          </Button>
        </div>
        <ConfirmDialog
          abierto={dialogo === "ok"}
          onCerrar={() => setDialogo(null)}
          onConfirmar={() => esperar(1200)}
          titulo="¿Cancelar el evento?"
          descripcion="Va a dejar de aparecer en el mapa y en las búsquedas. No se puede deshacer."
          textoConfirmar="Cancelar evento"
          textoProcesando="Cancelando..."
          variante="destructive"
        />
        <ConfirmDialog
          abierto={dialogo === "falla"}
          onCerrar={() => setDialogo(null)}
          onConfirmar={async () => {
            await esperar(800);
            throw new ApiError(409, "Solo se pueden cancelar eventos en borrador o publicados.");
          }}
          titulo="¿Ocultar el evento?"
          descripcion="Simula una respuesta 409 del backend: el error se muestra y el diálogo queda abierto."
          textoConfirmar="Ocultar"
        />
      </Seccion>

      <Seccion titulo="SelectorUbicacion (features/ubicacion)">
        <SelectorUbicacion
          valor={punto}
          onCambiar={(nuevo, { lugar }) => {
            setPunto(nuevo);
            setLugarBuscado(lugar?.nombre ?? null);
          }}
          error={errorUbicacion && !punto ? "Marcá dónde es el evento." : null}
        />
        <div className="catalogo-fila catalogo-selector-acciones">
          <Button variant="outline" size="sm" onClick={() => setErrorUbicacion((valor) => !valor)}>
            {errorUbicacion ? "Sin error" : "Simular error sin punto"}
          </Button>
          <Button variant="ghost" size="sm" onClick={() => setPunto(null)}>
            Quitar el punto
          </Button>
        </div>
        <pre className="catalogo-valor">
          {JSON.stringify({ valor: punto, lugarBuscado }, null, 2)}
        </pre>
      </Seccion>
    </div>
  );
};

export default CatalogoComponentes;
