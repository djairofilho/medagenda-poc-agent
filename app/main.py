"""FastAPI composition root."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import config
from app.appointments.router import router as appointments_router
from app.availability.router import router as availability_router
from app.conversations.llm import LangChainModel
from app.conversations.router import router as conversations_router
from app.conversations.service import ConversationService
from app.infrastructure.database import make_session_factory
from app.infrastructure.checkpoints import open_checkpointer
from app.observability.tracing import make_tracer


def create_app(*, database_url: str | None = None, checkpoint_url: str | None = None,
               model=None, tracer=None) -> FastAPI:
    database_url = database_url or config.DATABASE_URL
    checkpoint_url = checkpoint_url or (config.CHECKPOINT_DATABASE_URL if database_url == config.DATABASE_URL else None) or database_url
    engine, session_factory = make_session_factory(database_url)

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        active_tracer = tracer if tracer is not None else make_tracer()
        try:
            with open_checkpointer(checkpoint_url) as checkpointer:
                application.state.session_factory = session_factory
                application.state.conversations = ConversationService(
                    model=model or LangChainModel(), session_factory=session_factory,
                    checkpointer=checkpointer, tracer=active_tracer,
                )
                yield
        finally:
            if active_tracer:
                active_tracer.shutdown()
            engine.dispose()

    application = FastAPI(
        title=config.API_TITLE, version=config.API_VERSION,
        description=config.API_DESCRIPTION, lifespan=lifespan,
    )
    application.add_middleware(
        CORSMiddleware, allow_origins=["*"], allow_credentials=True,
        allow_methods=["*"], allow_headers=["*"],
    )
    application.include_router(conversations_router)
    application.include_router(appointments_router)
    application.include_router(availability_router)

    @application.get("/")
    def root():
        return {
            "message": "medAgenda API - Appointment Scheduling Agent",
            "version": config.API_VERSION,
            "endpoints": {
                "chat": "POST /chat",
                "appointments": "GET /appointments",
                "appointment_detail": "GET /appointments/{id}",
                "reset_session": "POST /sessions/{session_id}/reset",
                "list_slots": "GET /slots",
                "create_slots": "POST /slots",
                "delete_slots": "DELETE /slots",
            },
        }

    return application


app = create_app()
