from enum import Enum
from typing import Dict, Literal, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

class WorkflowType(str, Enum):
    SINGLE_CELL = "single_cell"
    #TODO: add more types

class ResultType(str, Enum):
    EMBEDDING = "embedding"
    EMBEDDINGS = "embeddings"
    VISUALIZATION = "visualization"
    RAW_DATA = "raw_data"

class SingleCellWorkflowConfig(BaseModel):
    input_file: str = Field(..., description="H5AD file containing single-cell data")
    model_id: Literal["scgpt", "geneformer"] = Field(
        ..., 
        description="Model to use for embedding generation"
    )
    embedding_mode: Literal["cls", "cell", "gene"] = Field(
        default="cls",
        description="Mode for embedding generation"
    )

    model_config = {
        'protected_namespaces': ()
    }

class WorkflowStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class WorkflowState(BaseModel):
    workflow_id: str
    created_at: datetime = Field(default_factory=datetime.now)
    status: WorkflowStatus = Field(default=WorkflowStatus.PENDING)
    progress: float = Field(default=0.0)
    error: Optional[str] = None
    result: Optional[Dict] = None
    model_config = {
        'protected_namespaces': ()
    }

class ResultMetadata(BaseModel):
    result_id: str
    workflow_id: str
    type: ResultType
    created_at: datetime = Field(default_factory=datetime.utcnow)
    file_path: str
    file_size: Optional[int] = None
    content_type: str

class WorkflowResultItem(BaseModel):
    """Individual result item from a workflow"""
    result_id: str
    type: ResultType
    file_path: str
    content_type: str
    created_at: datetime = Field(default_factory=datetime.now)
    file_size: int = 0

class WorkflowResult(BaseModel):
    """Result of a workflow execution"""
    workflow_id: str
    status: WorkflowStatus
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    error_message: Optional[str] = None
    results: List[WorkflowResultItem] = [] 