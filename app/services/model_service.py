from app.models.definitions import ModelRegistry, ModelType
from typing import List, Dict, Optional

class ModelService:
    def __init__(self):
        self._registry = ModelRegistry()

    async def get_available_models(self, model_type: Optional[ModelType] = None) -> List[Dict]:
        models = self._registry.get_models(model_type)
        return [model.model_dump() for model in models]

    async def validate_model_for_input(self, model_id: str, file_format: str) -> bool:
        model = self._registry.get_model(model_id)
        if not model:
            return False
        return file_format in model.input_formats 