import pytest
from unittest.mock import Mock, patch, MagicMock
import os
from fastapi.testclient import TestClient
from app.main import app
from app.models.workflows import WorkflowStatus, ResultType, WorkflowResult, WorkflowResultItem
from app.services.single_cell_service import SingleCellService
from app.services.workflow_service import WorkflowService
from datetime import datetime

@pytest.fixture
def mock_workflow_service():
    """Create a mock workflow service"""
    service = Mock(spec=WorkflowService)

    return service    

@pytest.fixture
def mock_single_cell_service():
    """Create a mock single cell service"""
    service = Mock(spec=SingleCellService)
    
    return service    

@pytest.fixture
def client(mock_single_cell_service, mock_workflow_service):
    app.dependency_overrides = {
        SingleCellService: lambda: mock_single_cell_service, 
        WorkflowService: lambda: mock_workflow_service
    }

    yield TestClient(app)
    
    # Clear overrides after test
    app.dependency_overrides.clear()

# TODO: fix after workers introduction
def test_create_single_cell_workflow(client_with_mocks, mock_workflow_service, mock_single_cell_service, tmp_path):
    """Test creating a single-cell workflow"""
    # Create a mock h5ad file
    test_file = "test.h5ad"
    test_file_path = os.path.join(tmp_path, test_file)
    with open(test_file_path, "w") as f:
        f.write("mock data")
    
    # Setup mock response for workflow creation
    mock_workflow_service.create_single_cell_workflow.return_value = "test-id"
    
    # Test the endpoint
    with open(test_file_path, "rb") as f:
        response = client_with_mocks.post(
            "/api/v1/workflows/single-cell",
            files={"file": ("test.h5ad", f, "application/octet-stream")},
            data={"model_id": "scgpt"}
        )

    assert response.status_code == 200
    assert response.json()["id"] == "test-id"

def test_invalid_model_id(client):
    """Test validation of model_id"""
    response = client.post(
        "/api/v1/workflows/single-cell",
        json={
            "input_file": "test.h5ad",
            "model_id": "invalid_model",
            "embedding_mode": "cls"
        }
    )
    assert response.status_code == 422  # Validation error

def test_invalid_embedding_mode(client):
    """Test validation of embedding_mode"""
    response = client.post(
        "/api/v1/workflows/single-cell",
        json={
            "input_file": "test.h5ad",
            "model_id": "scgpt",
            "embedding_mode": "invalid_mode"
        }
    )
    assert response.status_code == 422 

# TODO: fix after workers introduction
def test_get_workflow_status(client_with_mocks, mock_workflow_service):
    """Test retrieving workflow status"""
    # Create a mock workflow result
    mock_result = {
        "id": "test-id",
        "status": WorkflowStatus.COMPLETED.value,
        "progress": 1.0,
        "error": None,
        "result": None,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "results": [{
            "result_id": "result-1",
            "type": ResultType.EMBEDDINGS.value,
            "file_path": "results/embeddings_test.pt",
            "file_size": 1000,
            "content_type": "application/octet-stream",
            "created_at": datetime.now().isoformat()
        }]
    }

    # Configure both get_workflow and get_workflow_status mocks
    mock_workflow_service.get_workflow.return_value = WorkflowResult(
        workflow_id="test-id",
        status=WorkflowStatus.COMPLETED,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    mock_workflow_service.get_workflow_status.return_value = mock_result

    response = client_with_mocks.get("/api/v1/workflows/test-id")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "test-id"
    assert data["status"] == WorkflowStatus.COMPLETED.value

def test_get_nonexistent_workflow(client_with_mocks, mock_workflow_service):
    """Test retrieving a nonexistent workflow"""
    mock_workflow_service.get_workflow.return_value = None

    response = client_with_mocks.get("/api/v1/workflows/nonexistent-id")
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

def test_download_workflow_result(client_with_mocks, mock_workflow_service, tmp_path):
    """Test downloading a workflow result"""
    test_file_path = os.path.join(tmp_path, "test_result.csv")
    with open(test_file_path, "w") as f:
        f.write("test,data\n1,2\n")
    
    mock_result = WorkflowResult(
        workflow_id="test-id",
        status=WorkflowStatus.COMPLETED,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        results=[
            WorkflowResultItem(
                result_id="result-1",
                type=ResultType.EMBEDDINGS,
                file_path=test_file_path,
                file_size=os.path.getsize(test_file_path),
                content_type="text/csv",
                created_at=datetime.now()
            )
        ],
        error_message=None
    )
    
    mock_workflow_service.get_workflow.return_value = mock_result

    # Mock FileResponse to avoid actual file operations during testing
    with patch("app.api.routes.workflows.FileResponse", return_value=MagicMock()) as mock_file_response:
        response = client_with_mocks.get("/api/v1/workflows/test-id/results/result-1/download")
        
        assert response.status_code == 200
        mock_file_response.assert_called_once() 