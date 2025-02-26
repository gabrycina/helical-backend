from uuid import uuid4
import helical
import anndata
import torch
from pathlib import Path
from app.models.workflows import (
    SingleCellWorkflowConfig,
    WorkflowStatus,
    WorkflowResult,
    ResultType,
    WorkflowResultItem
)
from app.core.config import get_settings
from app.services.workflow_service import get_workflow_service
from helical.models.scgpt.model import scGPT, scGPTConfig
from helical.models.geneformer.model import Geneformer, GeneformerConfig
import platform
import os

settings = get_settings()

class SingleCellService:
    def __init__(self):
        self._output_dir = settings.RESULTS_DIR
        self._output_dir.mkdir(exist_ok=True)
        
        # Determine the best available device
        self.device = self._get_device()
        print(f"Using device: {self.device}")
        
        # Pass device through the config
        self._models = {
            "scgpt": lambda: scGPT(
                configurer=scGPTConfig(
                    device=str(self.device),
                    emb_mode="cls"
                )
            ),
            "geneformer": lambda: Geneformer(
                configurer=GeneformerConfig(
                    device=str(self.device)
                )
            )
        }

    def _get_device(self) -> torch.device:
        """
        Get the best available device for computation.
        Prioritizes: Metal (Mac) > CUDA > CPU
        """
        if torch.cuda.is_available():
            return torch.device('cuda')
        return torch.device('cpu')

    async def create_workflow(
        self, 
        config: SingleCellWorkflowConfig
    ) -> WorkflowResult:
        workflow_service = get_workflow_service()
        
        # Create a new workflow
        workflow = workflow_service.create_workflow()
        workflow.status = WorkflowStatus.RUNNING
        workflow_service.update_workflow(workflow)
        
        try:
            print(f"Loading file: {config.input_file}")
            # Load data
            input_path = settings.UPLOAD_DIR / config.input_file
            data = anndata.read_h5ad(input_path)
            
            print(f"Initializing model: {config.model_id}")
            # Initialize model with device already configured
            model = self._models[config.model_id.lower()]()
            
            print("Processing data")
            # Process data (device handling should be done inside the model)
            processed_data = model.process_data(data)
            
            print("Generating embeddings")
            # Generate embeddings (device handling should be done inside the model)
            embeddings = model.get_embeddings(processed_data)
            
            # Save results
            output_file = f"{config.model_id}_embeddings_{workflow.workflow_id}.pt"
            output_path = self._output_dir / output_file
            torch.save(embeddings, output_path)

            # Add result metadata to workflow
            workflow.results.append(
                WorkflowResultItem(
                    result_id=str(uuid4()),
                    type=ResultType.EMBEDDINGS,
                    file_path=str(output_path),
                    file_size=output_path.stat().st_size,
                    content_type="application/octet-stream"
                )
            )

            workflow.status = WorkflowStatus.COMPLETED
            workflow_service.update_workflow(workflow)

            return workflow
            
        except Exception as e:
            workflow.status = WorkflowStatus.FAILED
            workflow.error_message = str(e)
            workflow_service.update_workflow(workflow)
            return workflow

_service_instance = None

def get_service_instance():
    global _service_instance
    if _service_instance is None:
        _service_instance = SingleCellService()
    return _service_instance 