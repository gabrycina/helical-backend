from uuid import uuid4
import anndata
import torch
from app.models.workflows import (
    WorkflowStatus,
)
from app.core.config import get_settings
from helical.models.scgpt.model import scGPT, scGPTConfig
from helical.models.geneformer.model import Geneformer, GeneformerConfig
import logging
from pathlib import Path

settings = get_settings()

logger = logging.getLogger(__name__)

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

    async def process_workflow(self, workflow_id: str, input_path: Path, model_id: str, state_manager):
        """Process a single workflow"""
        try:
            state_manager.update_status(workflow_id, WorkflowStatus.PROCESSING)
            state_manager.update_progress(workflow_id, 0.0)  # Initialize progress
            logger.info(f"Starting workflow {workflow_id} with progress 0.0")
            
            print(f"Loading file: {input_path}")
            data = anndata.read_h5ad(input_path)
            logger.info(f"About to update progress for {workflow_id} to 0.4")
            state_manager.update_progress(workflow_id, 0.4)  # 40% - Data loaded
            logger.info(f"Progress updated for {workflow_id}")
            
            print(f"Initializing model: {model_id}")
            model = self._models[model_id.lower()]()
            logger.info(f"About to update progress for {workflow_id} to 0.5")
            state_manager.update_progress(workflow_id, 0.5)  # 50% - Model initialized
            logger.info(f"Progress updated for {workflow_id}")
            
            print("Processing data")
            processed_data = model.process_data(data)
            logger.info(f"About to update progress for {workflow_id} to 0.7")
            state_manager.update_progress(workflow_id, 0.7)  # 70% - Data processed
            logger.info(f"Progress updated for {workflow_id}")
            
            print("Generating embeddings")
            embeddings = model.get_embeddings(processed_data)
            logger.info(f"About to update progress for {workflow_id} to 0.9")
            state_manager.update_progress(workflow_id, 0.9)  # 90% - Embeddings generated
            logger.info(f"Progress updated for {workflow_id}")
            
            # Save results
            output_file = f"{model_id}_embeddings_{workflow_id}.pt"
            output_path = settings.RESULTS_DIR / output_file
            torch.save(embeddings, output_path)
            
            result = {
                'result_id': str(uuid4()),
                'type': 'embeddings',
                'file_path': str(output_path),
                'file_size': output_path.stat().st_size,
                'content_type': 'application/octet-stream'
            }
            
            state_manager.set_result(workflow_id, result)
            logger.info(f"About to update progress for {workflow_id} to 1.0")
            state_manager.update_progress(workflow_id, 1.0)  # 100% - Complete
            
            return result
            
        except Exception as e:
            logger.error(f"Workflow {workflow_id} failed: {e}")
            state_manager.set_error(workflow_id, str(e))
            raise

_service_instance = None

def get_service_instance():
    global _service_instance
    if _service_instance is None:
        _service_instance = SingleCellService()
    return _service_instance 