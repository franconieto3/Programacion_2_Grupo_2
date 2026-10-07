"""CredentialsFactory, tal como la define el diagrama de clases entregado
por la catedra: `createCredentials(peticion: Request): Credentials`.

Interpretacion de `peticion`: el schema Pydantic ya validado por el endpoint
(el DTO de entrada), no el Request crudo de Starlette — asi se reutiliza la
validacion de tipos/formato que ya hizo Pydantic en vez de reparsear el body
a mano dentro de la factory. Es una suposicion de diseno documentada en el
plan de implementacion.
"""

from typing import overload

from app.auth.credentials import (
    Credentials,
    EmailCredentials,
    EmailRecoveryRequest,
    EmailRegistration,
)
from app.auth.schemas import LoginRequest, RecoverPasswordRequest, RegisterRequest

Peticion = RegisterRequest | LoginRequest | RecoverPasswordRequest


class CredentialsFactory:
    """Simple Factory: traduce cada DTO a sus credenciales de email concretas.

    `create_credentials` lo invocan directamente los endpoints /register,
    /login y /recover-password de app/auth/router.py. Los overloads le
    indican al type checker que credenciales concretas devuelve cada DTO."""

    @overload
    @staticmethod
    def create_credentials(peticion: RegisterRequest) -> EmailRegistration: ...

    @overload
    @staticmethod
    def create_credentials(peticion: LoginRequest) -> EmailCredentials: ...

    @overload
    @staticmethod
    def create_credentials(peticion: RecoverPasswordRequest) -> EmailRecoveryRequest: ...

    @staticmethod
    def create_credentials(peticion: Peticion) -> Credentials:
        if isinstance(peticion, RegisterRequest):
            return EmailRegistration(
                email=peticion.email,
                password=peticion.password,
                nombre=peticion.nombre,
                apellido=peticion.apellido,
            )
        if isinstance(peticion, LoginRequest):
            return EmailCredentials(email=peticion.email, password=peticion.password)
        if isinstance(peticion, RecoverPasswordRequest):
            return EmailRecoveryRequest(email=peticion.email)
        raise TypeError(f"Tipo de peticion no soportado: {type(peticion)!r}")
