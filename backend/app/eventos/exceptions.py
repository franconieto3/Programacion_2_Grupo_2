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


class EventoNoEncontradoError(EventoError):
    """No existe un evento con el id pedido."""

    def __init__(self) -> None:
        super().__init__('No se encontro el evento solicitado.')


class NoEsDuenioDelEventoError(EventoError):
    """El evento existe pero pertenece a otro organizador (o es de seed):
    solo su duenio puede editarlo o cancelarlo (RF-02.4)."""

    def __init__(self) -> None:
        super().__init__('Solo el organizador del evento puede modificarlo.')


class EventoNoEditableError(EventoError):
    """El evento esta CANCELADO u OCULTO y ya no se puede editar."""

    def __init__(self, estado: EstadoEvento) -> None:
        super().__init__(f'No se puede editar un evento {estado}.')
        self.estado = estado


class CategoriasInvalidasError(EventoError):
    """Alguno de los slugs pedidos no existe o no esta activo (RF-04.1)."""

    def __init__(self, slugs: list[str]) -> None:
        super().__init__(f'Categorias invalidas: {", ".join(slugs)}.')
        self.slugs = slugs


class FechasEventoInvalidasError(EventoError):
    """La fecha de fin no es posterior a la de inicio."""

    def __init__(self) -> None:
        super().__init__(
            'La fecha de fin tiene que ser posterior a la de inicio.'
        )
