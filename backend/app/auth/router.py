"""Endpoints HTTP del modulo de auth. El router es deliberadamente delgado:
arma Credentials con CredentialsFactory, delega la ejecucion en Auth (inyectado
via `Depends(get_auth)`), y traduce el resultado a un schema Pydantic.
/register, /login y /recover-password son exclusivos de la autenticacion por
email + contrasena local; un proveedor externo futuro tendra sus propios
endpoints. El manejo de errores esta centralizado en app/auth/error_handlers.py
(registrado en app/main.py)."""

from fastapi import APIRouter, Cookie, Depends, Response, status

from app.auth.credentials_factory import CredentialsFactory
from app.auth.dependencies import EmailAuth, get_auth, get_token_service
from app.auth.schemas import (
    GenericMessageResponse,
    LoginRequest,
    RecoverPasswordRequest,
    RegisterRequest,
    SessionInfoResponse,
    TokenResponse,
    UsuarioPublic,
)
from app.core.config import Settings, get_settings
from app.core.security.token_service import TokenService

router = APIRouter(prefix="/auth", tags=["auth"])

_REFRESH_COOKIE_NAME = "refresh_token"
_REFRESH_COOKIE_PATH = "/auth"


def _set_refresh_cookie(response: Response, refresh_token: str, settings: Settings) -> None:
    response.set_cookie(
        key=_REFRESH_COOKIE_NAME,
        value=refresh_token,
        max_age=settings.refresh_token_ttl_days * 24 * 60 * 60,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        domain=settings.cookie_domain,
        path=_REFRESH_COOKIE_PATH,
    )


@router.post("/register", response_model=UsuarioPublic, status_code=status.HTTP_201_CREATED)
async def register(
    peticion: RegisterRequest,
    auth: EmailAuth = Depends(get_auth),
) -> UsuarioPublic:
    credentials = CredentialsFactory.create_credentials(peticion)
    resultado = await auth.register(credentials)
    return UsuarioPublic(
        id=resultado.usuario_id,
        email=resultado.email,
        nombre=resultado.nombre,
        rol=resultado.rol,
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    peticion: LoginRequest,
    response: Response,
    auth: EmailAuth = Depends(get_auth),
    settings: Settings = Depends(get_settings),
) -> TokenResponse:
    credentials = CredentialsFactory.create_credentials(peticion)
    resultado = await auth.sign_in(credentials)
    _set_refresh_cookie(response, resultado.refresh_token, settings)
    return TokenResponse(
        access_token=resultado.access_token,
        usuario=UsuarioPublic(
            id=resultado.usuario_id,
            email=resultado.email,
            nombre=resultado.nombre,
            rol=resultado.rol,
        ),
    )


@router.post(
    "/recover-password",
    response_model=GenericMessageResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def recover_password(
    peticion: RecoverPasswordRequest,
    auth: EmailAuth = Depends(get_auth),
) -> GenericMessageResponse:
    credentials = CredentialsFactory.create_credentials(peticion)
    await auth.recover_password(credentials)
    # Mensaje identico exista o no el email registrado: evita enumeracion de
    # usuarios (ver EmailRecovery y el plan, seccion 9).
    return GenericMessageResponse(
        message=(
            "Si el email esta registrado, vas a recibir instrucciones "
            "para recuperar tu contrasena."
        )
    )


@router.post("/verify-session", response_model=SessionInfoResponse)
async def verify_session(auth: EmailAuth = Depends(get_auth)) -> SessionInfoResponse:
    """POST (no GET): puede tener efecto lateral (emitir un access token
    nuevo via silent refresh), asi que no deberia dispararse implicitamente
    (prefetch del navegador, <img>, etc.)."""
    resultado = await auth.verify_session()
    return SessionInfoResponse(
        usuario_id=resultado.usuario_id,
        email=resultado.email,
        rol=resultado.rol,
        expires_at=resultado.expires_at,
        access_token=resultado.refreshed_access_token,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    token_service: TokenService = Depends(get_token_service),
    settings: Settings = Depends(get_settings),
) -> None:
    """Fuera de la jerarquia Strategy: el diagrama de la catedra no define un
    metodo de logout y no hay variabilidad de comportamiento por metodo de
    auth que lo justifique como quinta interfaz. Cierra el gap con RF-01.3
    (poder cerrar sesion) revocando el refresh token vigente."""
    if refresh_token:
        await token_service.revoke_refresh_token(refresh_token)
    response.delete_cookie(
        key=_REFRESH_COOKIE_NAME, domain=settings.cookie_domain, path=_REFRESH_COOKIE_PATH
    )
