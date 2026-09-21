"""CredentialsFactory, tal como la define el diagrama de clases entregado
por la catedra: `createCredentials(peticion: Request): Credentials`.

Interpretacion de `peticion`: el schema Pydantic ya validado por el endpoint
(el DTO de entrada), no el Request crudo de Starlette — asi se reutiliza la
validacion de tipos/formato que ya hizo Pydantic en vez de reparsear el body
a mano dentro de la factory. Es una suposicion de diseno documentada en el
plan de implementacion.
"""

from app.auth.credentials import Credentials, EmailCredentials
from app.auth.schemas import LoginRequest, RecoverPasswordRequest, RegisterRequest

Peticion = RegisterRequest | LoginRequest | RecoverPasswordRequest


class CredentialsFactory:
    """Simple Factory: hoy solo produce EmailCredentials. Agregar un nuevo
    tipo de peticion (ej. login por telefono) es un `isinstance` mas en este
    metodo, sin tocar Auth ni las estrategias (OCP)."""

    @staticmethod
    def create_credentials(peticion: Peticion) -> Credentials:
        if isinstance(peticion, RegisterRequest):
            return EmailCredentials(
                usuario=peticion.email,
                password=peticion.password,
                nombre=peticion.nombre,
                rol=peticion.rol,
            )
        if isinstance(peticion, LoginRequest):
            return EmailCredentials(usuario=peticion.email, password=peticion.password)
        if isinstance(peticion, RecoverPasswordRequest):
            return EmailCredentials(usuario=peticion.email, password=None)
        raise TypeError(f"Tipo de peticion no soportado: {type(peticion)!r}")
