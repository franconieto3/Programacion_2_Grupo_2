import asyncio
from typing import Protocol, runtime_checkable

from argon2 import PasswordHasher as Argon2
from argon2.exceptions import VerifyMismatchError


@runtime_checkable
class PasswordHasher(Protocol):
    """Puerto de hashing de contrasenas (RNF-04.1: nunca texto plano).

    Interfaz async para no obligar a las estrategias a saber que la
    implementacion concreta es CPU-bound; la implementacion decide como
    resolverlo sin filtrar ese detalle a quien la consume (DIP).
    """

    async def hash(self, plain_password: str) -> str: ...

    async def verify(self, plain_password: str, password_hash: str) -> bool: ...


class Argon2PasswordHasher:
    """Unica implementacion hoy. El hashing Argon2 es CPU-bound (~50-150ms);
    se delega a un hilo aparte via asyncio.to_thread para no bloquear el
    event loop del worker ASGI."""

    def __init__(self) -> None:
        self._hasher = Argon2()

    async def hash(self, plain_password: str) -> str:
        return await asyncio.to_thread(self._hasher.hash, plain_password)

    async def verify(self, plain_password: str, password_hash: str) -> bool:
        def _verify() -> bool:
            try:
                self._hasher.verify(password_hash, plain_password)
                return True
            except VerifyMismatchError:
                return False

        return await asyncio.to_thread(_verify)
