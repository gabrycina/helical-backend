from typing import Dict, List, Optional
from enum import Enum
from pydantic import BaseModel

class ModelType(str, Enum):
    RNA = "rna"
    DNA = "dna"

class ModelConfig(BaseModel):
    name: str  # e.g., "scGPT", "Geneformer"
    type: ModelType  # RNA or DNA
    description: str
    version: str
    input_formats: List[str]
    requires_gpu: bool = False

class ModelRegistry:
    def __init__(self):
        self._models: Dict[str, ModelConfig] = {}
        self._load_models()

    def _load_models(self):
        # TODO: In a production environment, this should load from database or an alternative credible source
        # TODO: check with model cards the definitions
        self._models = {
            "helix-mrna": ModelConfig(
                id="helix-mrna",
                name="Helix-mRNA",
                description="RNA structure prediction model",
                type=ModelType.RNA,
                input_formats=["fasta", "fa"],
                requires_gpu=True,
                version="1.0.0"
            ),
            "mamba2-mrna": ModelConfig(
                id="mamba2-mrna",
                name="Mamba2-mRNA",
                description="RNA sequence model",
                type=ModelType.RNA,
                input_formats=["fasta", "fa", "txt"],
                requires_gpu=True,
                version="1.0.0"
            ),
            "geneformer": ModelConfig(
                id="geneformer",
                name="Geneformer",
                description="Gene expression model",
                type=ModelType.RNA,
                input_formats=["csv", "tsv", "h5adb"],
                requires_gpu=True,
                version="1.0.0"
            ),
            "scgpt": ModelConfig(
                id="scgpt",
                name="scGPT",
                description="Single-cell RNA model",
                type=ModelType.RNA,
                input_formats=["csv", "tsv", "h5adb"],
                requires_gpu=True,
                version="1.0.0"
            ),
            "uce": ModelConfig(
                id="uce",
                name="Universal Cell Embedding",
                description="Cell embedding model",
                type=ModelType.RNA,
                input_formats=["csv", "tsv"],
                requires_gpu=True,
                version="1.0.0"
            ),
            "hyenadna": ModelConfig(
                id="hyenadna",
                name="HyenaDNA",
                description="DNA sequence model",
                type=ModelType.DNA,
                input_formats=["fasta", "fa", "txt"],
                requires_gpu=True,
                version="1.0.0"
            ),
            "caduceus": ModelConfig(
                id="caduceus",
                name="Caduceus",
                description="DNA language model",
                type=ModelType.DNA,
                input_formats=["fasta", "fa", "txt"],
                requires_gpu=True,
                version="1.0.0"
            )
        }

    def get_models(self, model_type: Optional[ModelType] = None) -> List[ModelConfig]:
        if model_type:
            return [model for model in self._models.values() if model.type == model_type]
        return list(self._models.values())

    def get_model(self, model_id: str) -> Optional[ModelConfig]:
        return self._models.get(model_id) 