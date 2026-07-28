from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from codemuscle.api.errors import domain_error_handler
from codemuscle.api.router import api_router
from codemuscle.config import get_settings
from codemuscle.domain.exceptions import DomainError


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(settings.web_origin).rstrip("/")],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router)
    app.add_exception_handler(DomainError, domain_error_handler)  # type: ignore[arg-type]
    return app


app = create_app()
