from uuid import uuid4
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import json
import logging
import asyncio

from fastapi import UploadFile

from app.core.config import get_settings
from app.models.workflows import (
    WorkflowResult,
    WorkflowStatus,
    WorkflowResultItem
)
from app.services.single_cell_service import get_service_instance as get_single_cell_service
from app.services.workflow_state_manager import WorkflowStateManager

settings = get_settings()
logger = logging.getLogger(__name__)

class WorkflowService:
    """Service for managing workflows of any type"""
    
    def __init__(self):
        self._workflows = {}  # In-memory dictionary storage
        self._output_dir = settings.RESULTS_DIR
        self._output_dir.mkdir(exist_ok=True)
        
        # Create a directory for storing workflow metadata
        self._workflows_dir = settings.UPLOAD_DIR / "workflows"
        self._workflows_dir.mkdir(exist_ok=True)
        
        # Load existing workflows from disk
        self._load_workflows_from_disk()
        
        self._state_manager = WorkflowStateManager()
        self._processing_queue = asyncio.Queue()
        self._worker_task = None
        self._single_cell_service = get_single_cell_service()
    
    def _load_workflows_from_disk(self):
        """Load workflow data from JSON files on disk"""
        for workflow_file in self._workflows_dir.glob("*.json"):
            try:
                with open(workflow_file, "r") as f:
                    workflow_data = json.load(f)
                    
                # Convert the loaded data to a WorkflowResult object
                workflow_id = workflow_file.stem
                
                # Convert results data
                results = []
                for result in workflow_data.get("results", []):
                    results.append(WorkflowResultItem(
                        result_id=result["result_id"],
                        type=result["type"],
                        file_path=result["file_path"],
                        content_type=result["content_type"],
                        created_at=datetime.fromisoformat(result["created_at"]),
                        file_size=result.get("file_size", 0)
                    ))
                
                # Create the workflow result object
                self._workflows[workflow_id] = WorkflowResult(
                    workflow_id=workflow_id,
                    status=workflow_data["status"],
                    created_at=datetime.fromisoformat(workflow_data["created_at"]),
                    updated_at=datetime.fromisoformat(workflow_data["updated_at"]),
                    error_message=workflow_data.get("error_message"),
                    results=results
                )
                
            except Exception as e:
                print(f"Error loading workflow from {workflow_file}: {e}")
    
    def _save_workflow_to_disk(self, workflow_id: str, workflow: WorkflowResult):
        """Save workflow data to a JSON file on disk"""
        workflow_file = self._workflows_dir / f"{workflow_id}.json"
        
        # Convert the workflow object to a serializable dict
        workflow_data = {
            "workflow_id": workflow.workflow_id,
            "status": workflow.status.value,
            "created_at": workflow.created_at.isoformat(),
            "updated_at": workflow.updated_at.isoformat(),
            "error_message": workflow.error_message,
            "results": []
        }
        
        # Convert results to serializable dicts
        for result in workflow.results:
            workflow_data["results"].append({
                "result_id": result.result_id,
                "type": result.type,
                "file_path": result.file_path,
                "content_type": result.content_type,
                "created_at": result.created_at.isoformat(),
                "file_size": result.file_size
            })
        
        # Write to file
        with open(workflow_file, "w") as f:
            json.dump(workflow_data, f, indent=2)
    
    def create_workflow(self) -> WorkflowResult:
        """Create a new workflow and return its ID"""
        workflow_id = str(uuid4())
        now = datetime.now()
        
        workflow = WorkflowResult(
            workflow_id=workflow_id,
            status=WorkflowStatus.CREATED,
            created_at=now,
            updated_at=now,
            results=[]
        )
        
        self._workflows[workflow_id] = workflow
        self._save_workflow_to_disk(workflow_id, workflow)
        
        return workflow
    
    def update_workflow(self, workflow: WorkflowResult) -> WorkflowResult:
        """Update a workflow's status and results"""
        workflow.updated_at = datetime.now()
        self._workflows[workflow.workflow_id] = workflow
        self._save_workflow_to_disk(workflow.workflow_id, workflow)
        return workflow
    
    def get_workflow(self, workflow_id: str) -> Optional[WorkflowResult]:
        """Get a workflow by ID"""
        # First check in-memory cache
        workflow = self._workflows.get(workflow_id)
        
        # If not found in memory, try loading from disk
        if workflow is None:
            workflow_file = self._workflows_dir / f"{workflow_id}.json"
            if workflow_file.exists():
                try:
                    with open(workflow_file, "r") as f:
                        workflow_data = json.load(f)
                    
                    # Convert results data
                    results = []
                    for result in workflow_data.get("results", []):
                        results.append(WorkflowResultItem(
                            result_id=result["result_id"],
                            type=result["type"],
                            file_path=result["file_path"],
                            content_type=result["content_type"],
                            created_at=datetime.fromisoformat(result["created_at"]),
                            file_size=result.get("file_size", 0)
                        ))
                    
                    # Create the workflow result object
                    workflow = WorkflowResult(
                        workflow_id=workflow_id,
                        status=workflow_data["status"],
                        created_at=datetime.fromisoformat(workflow_data["created_at"]),
                        updated_at=datetime.fromisoformat(workflow_data["updated_at"]),
                        error_message=workflow_data.get("error_message"),
                        results=results
                    )
                    
                    # Cache in memory
                    self._workflows[workflow_id] = workflow
                    
                except Exception as e:
                    print(f"Error loading workflow {workflow_id}: {e}")
                    return None
        
        return workflow

    def get_workflows(self) -> List[WorkflowResult]:
        """Get all workflows sorted by creation date (newest first)"""
        workflows = list(self._workflows.values())
        
        # Then check disk for any workflows not in memory
        for workflow_file in self._workflows_dir.glob("*.json"):
            workflow_id = workflow_file.stem
            
            # Skip if already in memory
            if workflow_id in self._workflows:
                continue
                
            try:
                with open(workflow_file, "r") as f:
                    workflow_data = json.load(f)
                
                # Convert results data
                results = []
                for result in workflow_data.get("results", []):
                    results.append(WorkflowResultItem(
                        result_id=result["result_id"],
                        type=result["type"],
                        file_path=result["file_path"],
                        content_type=result["content_type"],
                        created_at=datetime.fromisoformat(result["created_at"]),
                        file_size=result.get("file_size", 0)
                    ))
                
                # Create and add workflow
                workflow = WorkflowResult(
                    workflow_id=workflow_id,
                    status=workflow_data["status"],
                    created_at=datetime.fromisoformat(workflow_data["created_at"]),
                    updated_at=datetime.fromisoformat(workflow_data["updated_at"]),
                    error_message=workflow_data.get("error_message"),
                    results=results
                )
                
                # Cache in memory and add to results
                self._workflows[workflow_id] = workflow
                workflows.append(workflow)
                
            except Exception as e:
                print(f"Error loading workflow {workflow_id}: {e}")
                continue
        
        return sorted(workflows, key=lambda w: w.created_at, reverse=True)

    async def start_worker(self):
        if self._worker_task is None:
            self._worker_task = asyncio.create_task(self._process_queue())
            logger.info("Background worker started")

    async def create_single_cell_workflow(self, workflow_id: str, file: UploadFile, model_id: str) -> str:
        """Queue a new single cell workflow"""
        try:
            # Create initial workflow state
            self._state_manager.create_workflow(workflow_id)
            
            # Create initial workflow result
            workflow = WorkflowResult(
                workflow_id=workflow_id,
                status=WorkflowStatus.PENDING,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                results=[]
            )
            self._workflows[workflow_id] = workflow
            self._save_workflow_to_disk(workflow_id, workflow)

            # Save uploaded file immediately
            input_path = settings.UPLOAD_DIR / file.filename
            content = await file.read()
            with open(input_path, 'wb') as f:
                f.write(content)
            
            # Queue for processing with file path instead of UploadFile
            await self._processing_queue.put(("single_cell", workflow_id, input_path, model_id))
            return workflow_id
        except Exception as e:
            logger.error(f"Error creating workflow: {e}")
            # Clean up any created resources on error
            if workflow_id in self._workflows:
                del self._workflows[workflow_id]
            self._state_manager.set_error(workflow_id, str(e))
            raise

    async def get_workflow_status(self, workflow_id: str) -> Dict:
        """Get current workflow status"""
        # Check workflow state first (for progress updates)
        state = self._state_manager.get_workflow(workflow_id)
        logger.debug(f"Got state for workflow {workflow_id}: {state}")
        
        # Check workflow result (for persistent data)
        workflow = self._workflows.get(workflow_id)
        logger.debug(f"Got workflow for {workflow_id}: {workflow}")
        
        # If we have neither state nor workflow, the workflow doesn't exist
        if not state and not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        # Combine data from both sources
        response = {
            "id": workflow_id,
            "status": (state and state.status.value) or (workflow and workflow.status.value) or WorkflowStatus.PENDING.value,
            "progress": float(state.progress if state else 1),
            "error": state.error if state else None,
            "result": state.result if state else None,
            "created_at": workflow.created_at.isoformat() if workflow else None,
            "updated_at": workflow.updated_at.isoformat() if workflow else None,
            "results": [
                {
                    "result_id": r.result_id,
                    "type": r.type,
                    "file_path": r.file_path,
                    "content_type": r.content_type,
                    "created_at": r.created_at.isoformat(),
                    "file_size": r.file_size
                } for r in workflow.results
            ] if workflow and workflow.results else []
        }
        logger.debug(f"Full status response for {workflow_id}: {response}")
        return response

    async def _process_queue(self):
        logger.info("Starting workflow queue processor")
        while True:
            try:
                logger.info("Waiting for workflows...")
                workflow_type, workflow_id, file, model_id = await self._processing_queue.get()
                logger.info(f"Processing workflow {workflow_id} of type {workflow_type}")
                
                if workflow_type == "single_cell":
                    try:
                        # Get existing workflow
                        workflow = self._workflows[workflow_id]
                        workflow.status = WorkflowStatus.PROCESSING
                        workflow.updated_at = datetime.now()
                        self._save_workflow_to_disk(workflow_id, workflow)
                        logger.info(f"Starting processing for workflow {workflow_id}")
                        
                        # Process the workflow
                        result = await self._single_cell_service.process_workflow(
                            workflow_id, 
                            file, 
                            model_id,
                            self._state_manager
                        )
                        
                        logger.info(f"Workflow {workflow_id} completed successfully")
                        # Create result item
                        result_item = WorkflowResultItem(
                            result_id=result['result_id'],
                            type=result['type'],
                            file_path=result['file_path'],
                            content_type=result['content_type'],
                            file_size=result['file_size'],
                            created_at=datetime.now()
                        )
                        
                        # Update workflow
                        workflow.results.append(result_item)
                        workflow.status = WorkflowStatus.COMPLETED
                        workflow.updated_at = datetime.now()
                        self._save_workflow_to_disk(workflow_id, workflow)
                        
                        # Update state manager with result
                        self._state_manager.set_result(workflow_id, result)
                        
                        logger.info(f"Saved result for workflow {workflow_id}: {result}")
                        
                    except Exception as e:
                        logger.error(f"Error processing workflow {workflow_id}: {e}")
                        if workflow_id in self._workflows:
                            workflow = self._workflows[workflow_id]
                            workflow.status = WorkflowStatus.FAILED
                            workflow.error_message = str(e)
                            workflow.updated_at = datetime.now()
                            self._save_workflow_to_disk(workflow_id, workflow)
                        self._state_manager.set_error(workflow_id, str(e))
                    finally:
                        self._processing_queue.task_done()
            except Exception as e:
                logger.error(f"Error in queue processor: {e}")

# Singleton instance
_workflow_service_instance = None

def get_workflow_service():
    global _workflow_service_instance
    if _workflow_service_instance is None:
        _workflow_service_instance = WorkflowService()
    return _workflow_service_instance 