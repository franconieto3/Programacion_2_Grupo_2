import { useRef, useState } from "react";
import Icono from "../../../components/ui/Icono";
import "./CalendarioRango.css";

// Calendario mensual para elegir un rango de fechas con clics (RF-03.4):
// 1. el primer clic elige un solo día (desde = hasta), que ya filtra;
// 2. un segundo clic posterior lo extiende hasta ese día (fecha de fin
//    opcional); uno anterior empieza de nuevo desde ahí;
// 3. con un rango completo, el siguiente clic vuelve a empezar.
//
// - desde / hasta: 'YYYY-MM-DD' o ''. onCambiar({ desde, hasta }).
// Las fechas se manejan como texto y en UTC para no correrse de día por la
// zona horaria. Teclado (patrón "grid" de ARIA): flechas mueven un día o una
// semana, Inicio/Fin la semana, RePág/AvPág el mes; Enter o espacio eligen.

const DIAS_SEMANA = ["Lu", "Ma", "Mi", "Ju", "Vi", "Sá", "Do"];
const formatoMes = new Intl.DateTimeFormat("es-AR", {
  month: "long",
  year: "numeric",
  timeZone: "UTC",
});
const formatoDiaLargo = new Intl.DateTimeFormat("es-AR", {
  weekday: "long",
  day: "numeric",
  month: "long",
  year: "numeric",
  timeZone: "UTC",
});

const aTexto = (fecha) => fecha.toISOString().slice(0, 10);
const aFecha = (texto) => new Date(`${texto}T00:00:00Z`);
const sumarDias = (texto, dias) => {
  const fecha = aFecha(texto);
  fecha.setUTCDate(fecha.getUTCDate() + dias);
  return aTexto(fecha);
};
// Primer día del mes de `texto`, desplazado `meses`.
const inicioMes = (texto, meses = 0) => {
  const fecha = aFecha(texto);
  return aTexto(new Date(Date.UTC(fecha.getUTCFullYear(), fecha.getUTCMonth() + meses, 1)));
};
const mismoMes = (a, b) => a.slice(0, 7) === b.slice(0, 7);

// Hoy en la zona del usuario (no en UTC: a las 22 h en Argentina ya es mañana en UTC).
function hoyLocal() {
  const ahora = new Date();
  const mes = String(ahora.getMonth() + 1).padStart(2, "0");
  const dia = String(ahora.getDate()).padStart(2, "0");
  return `${ahora.getFullYear()}-${mes}-${dia}`;
}

// 6 semanas de lunes a domingo que cubren el mes de `primerDia`.
function semanasDelMes(primerDia) {
  const diaSemana = (aFecha(primerDia).getUTCDay() + 6) % 7; // lunes = 0
  const inicio = sumarDias(primerDia, -diaSemana);
  return Array.from({ length: 6 }, (_, semana) =>
    Array.from({ length: 7 }, (_, dia) => sumarDias(inicio, semana * 7 + dia)),
  );
}

// Rango nuevo después de un clic en `dia`.
function siguienteRango({ desde, hasta }, dia) {
  const esperandoFin = desde && (!hasta || hasta === desde);
  if (esperandoFin && dia > desde) return { desde, hasta: dia };
  return { desde: dia, hasta: dia };
}

const CalendarioRango = ({ desde, hasta, onCambiar }) => {
  const hoy = hoyLocal();
  const [mes, setMes] = useState(() => inicioMes(desde || hoy));
  // Día con tabindex=0 (foco "itinerante" dentro de la grilla).
  const [enfocado, setEnfocado] = useState(desde || hoy);
  const grilla = useRef(null);

  // Si el día enfocado no está en el mes visible, la grilla igual tiene que
  // ser alcanzable con Tab: se usa el 1 del mes.
  const diaConFoco = mismoMes(enfocado, mes) ? enfocado : mes;
  const fin = hasta || desde; // solo "desde" (URL vieja) se marca como un día

  const enfocar = (dia) => {
    setEnfocado(dia);
    if (!mismoMes(dia, mes)) setMes(inicioMes(dia));
    requestAnimationFrame(() =>
      grilla.current?.querySelector(`[data-dia="${dia}"]`)?.focus(),
    );
  };

  const alPresionar = (evento, dia) => {
    const pasos = {
      ArrowLeft: () => sumarDias(dia, -1),
      ArrowRight: () => sumarDias(dia, 1),
      ArrowUp: () => sumarDias(dia, -7),
      ArrowDown: () => sumarDias(dia, 7),
      Home: () => sumarDias(dia, -((aFecha(dia).getUTCDay() + 6) % 7)),
      End: () => sumarDias(dia, 6 - ((aFecha(dia).getUTCDay() + 6) % 7)),
      PageUp: () => mover(dia, -1),
      PageDown: () => mover(dia, 1),
    };
    const paso = pasos[evento.key];
    if (!paso) return;
    evento.preventDefault();
    enfocar(paso());
  };

  const elegir = (dia) => {
    setEnfocado(dia);
    if (!mismoMes(dia, mes)) setMes(inicioMes(dia));
    onCambiar(siguienteRango({ desde, hasta }, dia));
  };

  const ayuda = !desde
    ? "Elegí un día, o el primero de un rango."
    : !hasta || hasta === desde
      ? "Elegí otro día si querés un rango (opcional)."
      : "Hacé clic en un día para empezar de nuevo.";

  return (
    <div className="calendario">
      <div className="calendario-encabezado">
        <button
          type="button"
          className="calendario-nav"
          aria-label="Mes anterior"
          onClick={() => setMes(inicioMes(mes, -1))}
        >
          <Icono nombre="chevron_left" />
        </button>
        <span className="calendario-mes" aria-live="polite">
          {formatoMes.format(aFecha(mes))}
        </span>
        <button
          type="button"
          className="calendario-nav"
          aria-label="Mes siguiente"
          onClick={() => setMes(inicioMes(mes, 1))}
        >
          <Icono nombre="chevron_right" />
        </button>
      </div>

      <table
        ref={grilla}
        className="calendario-grilla"
        role="grid"
        aria-label={`Fechas, ${formatoMes.format(aFecha(mes))}`}
      >
        <thead>
          <tr>
            {DIAS_SEMANA.map((dia) => (
              <th key={dia} scope="col" abbr={dia}>
                {dia}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {semanasDelMes(mes).map((semana) => (
            <tr key={semana[0]}>
              {semana.map((dia) => {
                const enRango = desde && dia >= desde && dia <= fin;
                const esInicio = dia === desde;
                const esFin = dia === fin;
                const clases = [
                  "calendario-dia",
                  !mismoMes(dia, mes) && "calendario-dia-fuera",
                  dia === hoy && "calendario-dia-hoy",
                  enRango && "calendario-dia-rango",
                  esInicio && "calendario-dia-inicio",
                  esFin && "calendario-dia-fin",
                ]
                  .filter(Boolean)
                  .join(" ");
                return (
                  <td key={dia} role="gridcell" aria-selected={Boolean(enRango)}>
                    <button
                      type="button"
                      className={clases}
                      data-dia={dia}
                      tabIndex={dia === diaConFoco ? 0 : -1}
                      aria-label={formatoDiaLargo.format(aFecha(dia))}
                      aria-current={dia === hoy ? "date" : undefined}
                      onClick={() => elegir(dia)}
                      onKeyDown={(evento) => alPresionar(evento, dia)}
                    >
                      {aFecha(dia).getUTCDate()}
                    </button>
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>

      <div className="calendario-pie">
        <p className="calendario-ayuda">{ayuda}</p>
        {desde && (
          <button
            type="button"
            className="calendario-borrar"
            onClick={() => onCambiar({ desde: "", hasta: "" })}
          >
            Borrar fechas
          </button>
        )}
      </div>
    </div>
  );
};

// Mismo día del mes `meses` después (o el último, si ese mes es más corto).
function mover(dia, meses) {
  const destino = inicioMes(dia, meses);
  const ultimo = sumarDias(inicioMes(dia, meses + 1), -1);
  const candidato = `${destino.slice(0, 8)}${dia.slice(8)}`;
  return candidato > ultimo ? ultimo : candidato;
}

export default CalendarioRango;
