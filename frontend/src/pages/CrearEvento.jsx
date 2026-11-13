import { useQueryClient } from "@tanstack/react-query";
import { useLocation, useNavigate } from "react-router-dom";
import Button from "../components/ui/Button";
import { clavesEventos } from "../features/eventos/clavesEventos";
import FormularioEvento from "../features/eventos/components/FormularioEvento";
import { crearEvento } from "../services/eventos";

// Alta de un evento (CU-03, RF-02.1 a RF-02.3). Solo para organizadores
// aprobados (OrganizadorRoute). El evento se publica directo: al crearlo se va
// a su ficha, reemplazando esta página en el historial para que "Volver" no
// traiga de nuevo el formulario.
const CrearEvento = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const queryClient = useQueryClient();

  const publicar = async (datos) => {
    const evento = await crearEvento(datos);
    // El mapa, la lista y "Mis eventos" lo tienen que mostrar.
    await queryClient.invalidateQueries({ queryKey: clavesEventos.todas });
    navigate(`/eventos/${evento.id_evento}`, {
      replace: true,
      state: { aviso: "Publicaste el evento: ya aparece en el mapa y en las búsquedas." },
    });
  };

  const descartar = () => (location.key !== "default" ? navigate(-1) : navigate("/mis-eventos"));

  return (
    <div className="pagina">
      <h1 className="pagina-titulo">Crear evento</h1>
      <FormularioEvento onEnviar={publicar} textoEnviar="Publicar evento" textoEnviando="Publicando...">
        <Button type="button" variant="ghost" onClick={descartar}>
          Descartar
        </Button>
      </FormularioEvento>
    </div>
  );
};

export default CrearEvento;
