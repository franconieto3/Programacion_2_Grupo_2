// Qué puede hacer el usuario según sus roles (GET /auth/me). El backend igual
// valida cada acción: esto es para no ofrecer lo que va a responder 403.
// "Ser organizador" lleva a la solicitud: se ofrece sin perfil, con uno
// rechazado (puede volver a pedirlo) o pendiente (ahí ve que está en revisión).
// Aprobado no la necesita y suspendido no puede volver a pedirlo.
export function permisosDe(user) {
  const estadoOrganizador = user.organizador?.estado;
  const esOrganizador = estadoOrganizador === "APROBADO";
  return {
    esOrganizador,
    puedeSolicitar: !esOrganizador && estadoOrganizador !== "SUSPENDIDO",
    esAdmin: Boolean(user.es_admin),
  };
}
