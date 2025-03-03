from contextlib import asynccontextmanager
from fastapi import (
    APIRouter, 
    FastAPI, 
    HTTPException, 
    Depends, 
    UploadFile, 
    File,
    Query
)
from fastapi.responses import FileResponse
from pathlib import Path
from app.services.single_cell_service import get_service_instance as get_single_cell_service
from app.services.workflow_service import get_workflow_service
from app.models.workflows import WorkflowResult
from uuid import uuid4
from typing import Dict
import logging

router = APIRouter()
single_cell_service = get_single_cell_service()
workflow_service = get_workflow_service()
logger = logging.getLogger(__name__)

@asynccontextmanager #runs at startup
async def lifespan(app: FastAPI):
    await workflow_service.start_worker()
    yield

@router.post("/workflows/single-cell")
async def create_single_cell_workflow(
    file: UploadFile = File(..., description="Single cell file"),
    model_id: str = Query(..., description="Model ID to use")
) -> Dict[str, str]:
    try:        
        workflow_id = str(uuid4())
        await workflow_service.create_single_cell_workflow(workflow_id, file, model_id)
        return {"workflow_id": workflow_id}
    except Exception as e:
        logger.error(f"Error creating workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/workflows/{workflow_id}")
async def get_workflow_status(workflow_id: str) -> Dict:
    try:
        return await workflow_service.get_workflow_status(workflow_id)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found")
    except Exception as e:
        logger.error(f"Error getting workflow status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/workflows/{workflow_id}/results/{result_id}/download")
async def download_workflow_result(
    workflow_id: str,
    result_id: str,
    workflow_service = Depends(get_workflow_service)
):
    workflow = workflow_service.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
        
    result = next((r for r in workflow.results if r.result_id == result_id), None)
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")
        
    return FileResponse(
        path=result.file_path,
        filename=Path(result.file_path).name,
        media_type=result.content_type
    )
    
@router.get("/workflows", response_model=list[WorkflowResult])
async def get_workflows(
    workflow_service = Depends(get_workflow_service)
):
    """Get all workflows"""
    return workflow_service.get_workflows()
