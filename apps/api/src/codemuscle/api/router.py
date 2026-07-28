from fastapi import APIRouter

from codemuscle.api.routes.health import router as health_router
from codemuscle.api.routes.settings import router as settings_router
from codemuscle.api.routes.workspace import router as workspace_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health_router)
api_router.include_router(settings_router)
api_router.include_router(workspace_router)
