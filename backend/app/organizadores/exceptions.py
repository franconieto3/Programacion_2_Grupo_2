from app.organizadores.models import EstadoOrganizador

_MENSAJE_POR_ESTADO = {
    EstadoOrganizador.PENDIENTE: (
        'Ya tenes una solicitud de organizador en revision.'
    ),
    EstadoOrganizador.APROBADO: 'Ya tenes un perfil de organizador aprobado.',
}


class OrganizadorError(Exception):
    """Base de todas las excepciones del dominio de organizadores."""


class SolicitudYaExistenteError(OrganizadorError):
    """El usuario ya tiene un perfil PENDIENTE o APROBADO (CU-04). Sin
    estado cuando la detecta la base (UNIQUE sobre id_usuario) por dos
    solicitudes simultaneas."""

    def __init__(self, estado: EstadoOrganizador | None = None) -> None:
        super().__init__(
            _MENSAJE_POR_ESTADO.get(
                estado, 'Ya existe una solicitud de organizador.'
            )
        )
        self.estado = estado


class OrganizadorSuspendidoError(OrganizadorError):
    """Un perfil SUSPENDIDO no puede volver a solicitarse: si pudiera, la
    suspension se esquivaria pidiendo de nuevo."""

    def __init__(self) -> None:
        super().__init__(
            'Tu perfil de organizador esta suspendido. '
            'No podes volver a solicitarlo.'
        )
