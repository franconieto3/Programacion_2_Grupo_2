"""`Credentials` (tipo base abstracto) y las credenciales concretas de email.

Cada metodo de autenticacion tiene datos muy distintos (email + contrasena,
token OAuth, etc.), asi que `Credentials` NO intenta unificarlos en un
diccionario comun: cada subclase declara sus propios atributos tipados y cada
estrategia declara, via genericos, que credenciales concretas acepta (ver
app/auth/behaviors/base.py). Lo unico comun es `identifier`, la identidad de
quien intenta autenticarse (la usa RateLimitedSignIn como clave).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from app.models.usuario import RolEnum


class Credentials(ABC):
    @property
    @abstractmethod
    def identifier(self) -> str:
        """Identidad de quien se autentica (ej. el email)."""


@dataclass(frozen=True, slots=True)
class EmailCredentials(Credentials):
    """Login con email + contrasena local."""

    email: str
    password: str = field(repr=False)

    @property
    def identifier(self) -> str:
        return self.email


@dataclass(frozen=True, slots=True)
class EmailRegistration(Credentials):
    """Alta con email + contrasena local, mas los datos del perfil."""

    email: str
    password: str = field(repr=False)
    nombre: str
    rol: RolEnum

    @property
    def identifier(self) -> str:
        return self.email


@dataclass(frozen=True, slots=True)
class EmailRecoveryRequest(Credentials):
    """Pedido de recuperacion de contrasena: solo se conoce el email."""

    email: str

    @property
    def identifier(self) -> str:
        return self.email
