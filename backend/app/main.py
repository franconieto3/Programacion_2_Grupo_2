"""Punto de entrada de la app. Arma la instancia de FastAPI, registra el
router de auth, los exception handlers, y suscribe los observers al
AuthEventPublisher (Singleton) una unica vez en el arranque -- no en cada
request."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth.audit_repository import SQLAlchemyAuditLogWriter
from app.auth.dependencies import get_auth_event_publisher
from app.auth.error_handlers import register_auth_exception_handlers
from app.auth.events.observers.audit_log_observer import AuditLogObserver
from app.auth.events.observers.email_notification_observer import EmailNotificationObserver
from app.auth.router import router as auth_router
from app.core.email_sender import ConsoleEmailSender
from app.db.session import async_session_factory

logging.basicConfig(level=logging.INFO)


class _StandaloneAuditLogWriter:
    """AuditLogObserver se suscribe UNA VEZ en el arranque, no por request,
    asi que no puede depender de la sesion de una request en particular. Abre
    y cierra su propia sesion corta en cada evento (ver
    app/auth/audit_repository.py para la escritura real)."""

    async def record(self, *, event_type: str, email: str | None, detalle: str) -> None:
        async with async_session_factory() as session:
            writer = SQLAlchemyAuditLogWriter(session)
            await writer.record(event_type=event_type, email=email, detalle=detalle)
            await session.commit()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    publisher = get_auth_event_publisher()
    publisher.subscribe(EmailNotificationObserver(ConsoleEmailSender()))
    publisher.subscribe(AuditLogObserver(_StandaloneAuditLogWriter()))
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="Eventos API", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],  # frontend Vite en dev, ver docs/planning.md
        allow_credentials=True,  # imprescindible para que el navegador mande la cookie de refresh
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_auth_exception_handlers(app)
    app.include_router(auth_router)

    return app


app = create_app()
