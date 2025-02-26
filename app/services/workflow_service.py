from uuid import uuid4
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import json

from app.core.config import get_settings
from app.models.workflows import (
    WorkflowResult,
    WorkflowStatus,
    WorkflowResultItem
)

settings = get_settings()

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
            "status": workflow.status,
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


# Singleton instance
_workflow_service_instance = None

def get_workflow_service():
    global _workflow_service_instance
    if _workflow_service_instance is None:
        _workflow_service_instance = WorkflowService()
    return _workflow_service_instance 