from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from presentation.api.routes.health import router as health_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Anki Generator API",
        description="API for generating Anki decks",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Middleware Registration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Router Registration
    app.include_router(health_router)

    return app