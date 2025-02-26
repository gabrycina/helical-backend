from fastapi import APIRouter
from .models import router as models_router
from .upload import router as upload_router
from .workflows import router as workflows_router

router = APIRouter()

router.include_router(upload.router, tags=["upload"])
router.include_router(models.router, tags=["models"])
router.include_router(workflows.router, tags=["workflows"]) 