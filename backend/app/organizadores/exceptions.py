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


class OrganizadorNoEncontradoError(OrganizadorError):
    """No existe un organizador con el id pedido (CU-05)."""

    def __init__(self) -> None:
        super().__init__('No se encontro el organizador solicitado.')


class OrganizadorNoAprobadoError(OrganizadorError):
    """El usuario no tiene perfil de organizador o no esta APROBADO, asi que
    no puede crear ni gestionar eventos (RF-01.7)."""

    def __init__(self) -> None:
        super().__init__(
            'Necesitas un perfil de organizador aprobado para gestionar '
            'eventos.'
        )


class TransicionEstadoInvalidaError(OrganizadorError):
    """El organizador no esta en un estado desde el que la accion pedida
    (aprobar/rechazar/suspender) sea valida (CU-05)."""

    def __init__(
        self, estado_actual: EstadoOrganizador, estado_destino: EstadoOrganizador
    ) -> None:
        super().__init__(
            f'No se puede pasar de {estado_actual} a {estado_destino}.'
        )
        self.estado_actual = estado_actual
        self.estado_destino = estado_destino
