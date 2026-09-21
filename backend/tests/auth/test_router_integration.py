"""Integracion del router HTTP contra la app real de FastAPI, con las
dependencias de persistencia reemplazadas por dobles en memoria via
`app.dependency_overrides` (DIP en accion: ni Auth ni las estrategias se
tocan para testear el layer HTTP).

No usa una base de datos real (ni siquiera SQLite): eso queda como un test
adicional, mas costoso, sobre SQLAlchemyUserRepository en aislamiento
(ver seccion 10 del plan de auth)."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.auth.dependencies import (
    get_auth_event_publisher,
    get_reset_token_repository,
    get_token_service,
    get_user_repository,
)
from app.auth.events.publisher import AuthEventPublisher
from app.main import app
from tests.conftest import FakeTokenService, InMemoryResetTokenRepository, InMemoryUserRepository


@pytest.fixture
def wired_app():
    user_repository = InMemoryUserRepository()
    token_service = FakeTokenService()
    reset_repo = InMemoryResetTokenRepository()
    publisher = AuthEventPublisher()

    app.dependency_overrides[get_user_repository] = lambda: user_repository
    app.dependency_overrides[get_token_service] = lambda: token_service
    app.dependency_overrides[get_reset_token_repository] = lambda: reset_repo
    app.dependency_overrides[get_auth_event_publisher] = lambda: publisher

    yield user_repository, token_service

    app.dependency_overrides.clear()


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def test_register_then_login_then_verify_session(wired_app):
    user_repository, token_service = wired_app
    async with _client() as client:
        register_response = await client.post(
            "/auth/register",
            json={"email": "a@a.com", "password": "secret123", "nombre": "Ana", "rol": "DEMANDANTE"},
        )
        assert register_response.status_code == 201
        assert register_response.json()["email"] == "a@a.com"

        # FakeTokenService necesita conocer al usuario para poder resolver
        # sus tokens; SQLAlchemyUserRepository/JoseTokenService reales no
        # necesitan este paso (consultan la base de datos).
        usuario = await user_repository.get_by_email("a@a.com")
        token_service.register_user(usuario)

        login_response = await client.post(
            "/auth/login", json={"email": "a@a.com", "password": "secret123"}
        )
        assert login_response.status_code == 200
        body = login_response.json()
        assert body["access_token"]
        set_cookie_headers = login_response.headers.get_list("set-cookie")
        assert any("refresh_token=" in h and "HttpOnly" in h for h in set_cookie_headers)

        verify_response = await client.post(
            "/auth/verify-session",
            headers={"Authorization": f"Bearer {body['access_token']}"},
        )
        assert verify_response.status_code == 200
        assert verify_response.json()["email"] == "a@a.com"


async def test_login_with_wrong_password_returns_401(wired_app):
    async with _client() as client:
        await client.post(
            "/auth/register",
            json={"email": "a@a.com", "password": "secret123", "nombre": "Ana", "rol": "DEMANDANTE"},
        )
        response = await client.post("/auth/login", json={"email": "a@a.com", "password": "mala"})

        assert response.status_code == 401


async def test_register_with_duplicate_email_returns_409(wired_app):
    async with _client() as client:
        payload = {
            "email": "a@a.com",
            "password": "secret123",
            "nombre": "Ana",
            "rol": "DEMANDANTE",
        }
        await client.post("/auth/register", json=payload)
        response = await client.post("/auth/register", json=payload)

        assert response.status_code == 409


async def test_recover_password_responds_identically_for_existing_and_unknown_email(wired_app):
    async with _client() as client:
        await client.post(
            "/auth/register",
            json={"email": "a@a.com", "password": "secret123", "nombre": "Ana", "rol": "DEMANDANTE"},
        )

        r1 = await client.post("/auth/recover-password", json={"email": "a@a.com"})
        r2 = await client.post("/auth/recover-password", json={"email": "nadie@a.com"})

        assert r1.status_code == r2.status_code == 202
        assert r1.json() == r2.json()


async def test_verify_session_without_any_token_returns_401(wired_app):
    async with _client() as client:
        response = await client.post("/auth/verify-session")

        assert response.status_code == 401
