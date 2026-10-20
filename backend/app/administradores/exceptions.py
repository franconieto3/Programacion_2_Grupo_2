class AdministradorError(Exception):
    """Base de todas las excepciones del dominio de administradores."""


class NoEsAdministradorError(AdministradorError):
    """El usuario autenticado no tiene perfil de administrador."""

    def __init__(self) -> None:
        super().__init__('Esta accion requiere permisos de administrador.')
