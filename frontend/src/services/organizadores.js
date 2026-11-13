// Endpoints de /organizadores del backend (app/organizadores/router.py).
// Requieren sesión iniciada.

import { api } from './client'

// CU-04 (RF-01.6). datos: { nombre_publico, descripcion }.
// La solicitud queda PENDIENTE hasta que la revise un administrador. Devuelve
// { id_organizador, id_usuario, nombre_publico, descripcion, estado, fecha_creacion }.
// Errores: 409 si ya tiene una solicitud PENDIENTE o un perfil APROBADO,
// 403 si el perfil está SUSPENDIDO. Un perfil RECHAZADO puede volver a pedirlo.
export function solicitarOrganizador(datos) {
  return api.post('/organizadores/solicitud', datos)
}
