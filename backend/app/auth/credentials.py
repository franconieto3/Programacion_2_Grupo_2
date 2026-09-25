"""Credentials <<abstracta>> / EmailCredentials, tal como los define el
diagrama de clases entregado por la catedra."""

from abc import ABC, abstractmethod
from typing import TypedDict

from app.models.usuario import RolEnum


class CredentialsData(TypedDict, total=False):
    usuario: str
    password: str | None
    nombre: str
    rol: RolEnum
    # Datos de proveedores OAuth (Google/Facebook). Opcionales (total=False):
    # EmailCredentials no los emite y las credenciales OAuth no emiten
    # `password`, sin romper el contrato get_credentials() -> CredentialsData.
    oauth_token: str
    provider: str


class Credentials(ABC):
    """Abstraccion que permite a cada estrategia (Behavior) operar sobre
    credenciales sin conocer su representacion concreta. Hoy solo existe
    EmailCredentials; las credenciales OAuth (GoogleCredentials,
    FacebookCredentials) las crea la fabrica de su familia
    (app/auth/factories.py) y las estrategias existentes no cambian (OCP/DIP)."""

    @abstractmethod
    def get_credentials(self) -> CredentialsData: ...


class EmailCredentials(Credentials):
    """Fiel al diagrama: atributos privados `usuario` (el email) y
    `password`. Se agregan `nombre`/`rol` opcionales para poder transportar
    los datos de alta de RegisterRequest sin crear una clase de credenciales
    nueva no contemplada en el diagrama (ver docs/planning.md / plan de auth,
    seccion 3, para la justificacion completa).

    Para recover-password, `password` queda en None: `usuario` sigue
    interpretandose siempre como el email en los tres flujos que usan esta
    clase (login, registro, recuperacion).
    """

    def __init__(
        self,
        usuario: str,
        password: str | None = None,
        nombre: str | None = None,
        rol: RolEnum | None = None,
    ) -> None:
        self._usuario = usuario
        self._password = password
        self._nombre = nombre
        self._rol = rol

    def get_credentials(self) -> CredentialsData:
        data: CredentialsData = {"usuario": self._usuario, "password": self._password}
        if self._nombre is not None:
            data["nombre"] = self._nombre
        if self._rol is not None:
            data["rol"] = self._rol
        return data
