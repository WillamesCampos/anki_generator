from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import exceptions as exc_handlers
from app.errors import BaseAPIException, InternalServerError, NotFoundError, ValidationError
from app.routes.decks import router as decks_router
from app.routes.health import router as health_router

# `<regra_obrigatoria id="versionamento-url">`: toda URL DEVE ser versionada,
# incluindo health checks, em todos os serviços (não só no Django).
API_PREFIX = "/document-generator/v1"


def create_app() -> FastAPI:
    app = FastAPI(
        title="Document Generator API",
        description="Microsserviço de geração de documentos (relatórios PDF, exportação Anki)",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_exception_handler(BaseAPIException, exc_handlers.base_exception_handler)
    app.add_exception_handler(ValidationError, exc_handlers.validation_exception_handler)
    app.add_exception_handler(NotFoundError, exc_handlers.not_found_exception_handler)
    app.add_exception_handler(
        InternalServerError, exc_handlers.internal_server_error_exception_handler
    )

    app.include_router(health_router, prefix=API_PREFIX)
    app.include_router(decks_router, prefix=API_PREFIX)

    return app


app = create_app()
