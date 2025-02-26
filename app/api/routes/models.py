from functools import lru_cache
from fastapi import APIRouter, Depends
from typing import Dict, List, Optional
from app.models.definitions import ModelType
from app.services.model_service import ModelService

router = APIRouter()

@lru_cache()
def get_model_service() -> ModelService:
    """
    Dependency that provides a ModelService instance.
    Cached to avoid creating multiple instances.
    """
    return ModelService() 

@router.get("/models")
async def get_models(
    model_type: Optional[ModelType] = None,
    service: ModelService = Depends(get_model_service)
) -> Dict[str, List]:
    """
    Get available models, optionally filtered by type
    """
    models = await service.get_available_models(model_type)
    return {"models": models} 