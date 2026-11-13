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

// --- Administración (RF-05.5, CU-05). Solo administradores: si no, 403. ---
// Devuelven el organizador con la forma de solicitarOrganizador(). Un estado
// que no permite la acción responde 409 (aprobar y rechazar solo desde
// PENDIENTE; suspender solo desde APROBADO).

// estado: 'PENDIENTE' | 'APROBADO' | 'RECHAZADO' | 'SUSPENDIDO'. Las más
// antiguas primero, para revisarlas en el orden en que llegaron. Sin
// paginación. No incluye el nombre ni el email del usuario: solo id_usuario.
export function listarOrganizadores(estado, { signal } = {}) {
  return api.get('/admin/organizadores', { query: { estado }, signal })
}

export function aprobarOrganizador(idOrganizador) {
  return api.post(`/admin/organizadores/${idOrganizador}/aprobar`)
}

export function rechazarOrganizador(idOrganizador) {
  return api.post(`/admin/organizadores/${idOrganizador}/rechazar`)
}

export function suspenderOrganizador(idOrganizador) {
  return api.post(`/admin/organizadores/${idOrganizador}/suspender`)
}
