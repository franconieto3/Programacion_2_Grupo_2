from app.eventos.models import EstadoEvento


class EventoError(Exception):
    """Base de todas las excepciones del dominio de eventos."""


class TransicionEstadoEventoInvalidaError(EventoError):
    """El evento no esta en un estado desde el que la accion pedida
    (cancelar/ocultar) sea valida."""

    def __init__(
        self, estado_actual: EstadoEvento, estado_destino: EstadoEvento
    ) -> None:
        super().__init__(
            f'No se puede pasar de {estado_actual} a {estado_destino}.'
        )
        self.estado_actual = estado_actual
        self.estado_destino = estado_destino
