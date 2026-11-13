import { yaTermino } from './formato'

const MODIFICABLES = ['BORRADOR', 'PUBLICADO']
// Un cancelado también se puede ocultar: baja la ficha si tiene contenido inapropiado.
const OCULTABLES = ['PUBLICADO', 'CANCELADO']

// Qué puede hacer el usuario con un evento (RF-01.7, RF-02.4, RF-05.1). El backend
// igual valida cada acción (403 si no es el dueño, 409 si el estado no lo
// permite): esto es para no ofrecer botones que van a fallar.
// - esPropio: lo publicó su perfil de organizador, y está APROBADO.
// - puedeEditar: propio y en BORRADOR o PUBLICADO (aunque ya haya terminado,
//   p. ej. para corregir un dato).
// - puedeCancelar: además, que no haya terminado: cancelar algo que ya pasó
//   no le avisa nada a nadie.
// - puedeOcultar: es administrador y el evento está PUBLICADO o CANCELADO
//   (moderación; no hace falta que sea suyo).
export function permisosSobre(evento, usuario) {
  const organizador = usuario?.organizador
  const esPropio =
    organizador?.estado === 'APROBADO' &&
    evento.id_organizador != null &&
    evento.id_organizador === organizador.id_organizador
  const puedeEditar = esPropio && MODIFICABLES.includes(evento.estado)
  return {
    esPropio,
    puedeEditar,
    puedeCancelar: puedeEditar && !yaTermino(evento),
    puedeOcultar: Boolean(usuario?.es_admin) && OCULTABLES.includes(evento.estado),
  }
}
