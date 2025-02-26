from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from pathlib import Path
from app.services.single_cell_service import get_service_instance as get_single_cell_service
from app.services.workflow_service import get_workflow_service
from app.models.workflows import (
    SingleCellWorkflowConfig, 
    WorkflowResult
)

router = APIRouter()

@router.post("/workflows/single-cell", response_model=WorkflowResult)
async def create_single_cell_workflow(
    config: SingleCellWorkflowConfig,
    service = Depends(get_single_cell_service)
):
    """
    Create and execute a single-cell workflow
    """
    return await service.create_workflow(config)

@router.get("/workflows/{workflow_id}", response_model=WorkflowResult)
async def get_workflow_status(
    workflow_id: str,
    workflow_service = Depends(get_workflow_service)
):
    """Get the status of a workflow"""
    result = workflow_service.get_workflow(workflow_id)
    if not result:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return result

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
