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

def test_create_single_cell_workflow(client_with_mocks, mock_single_cell_service, tmp_path):
    """Test creating a single-cell workflow"""
    # Create a mock h5ad file
    test_file = "test.h5ad"
    test_file_path = os.path.join(tmp_path, test_file)
    with open(test_file_path, "w") as f:
        f.write("mock data")
    
    # Setup mock response
    mock_result = WorkflowResult(
        workflow_id="test-id",
        status=WorkflowStatus.COMPLETED,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        results=[
            WorkflowResultItem(
                result_id="result-1",
                type=ResultType.EMBEDDINGS,
                file_path="uploads/results/scgpt_embeddings.pt",
                file_size=1000,
                content_type="application/octet-stream",
                created_at=datetime.now()
            )
        ],
        error_message=None
    )
    
    # Configure the mock
    mock_single_cell_service.create_workflow.return_value = mock_result

    # Test the endpoint
    response = client_with_mocks.post(
        "/api/v1/workflows/single-cell",
        json={
            "input_file": test_file,
            "model_id": "scgpt",
            "embedding_mode": "cls"
        }
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["workflow_id"] == "test-id"
    assert response_data["status"] == "completed"
    assert len(response_data["results"]) == 1

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

def test_get_workflow_status(client_with_mocks, mock_workflow_service):
    """Test retrieving workflow status"""
    # Create a mock workflow result
    mock_result = WorkflowResult(
        workflow_id="test-id",
        status=WorkflowStatus.COMPLETED,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        results=[
            WorkflowResultItem(
                result_id="result-1",
                type=ResultType.EMBEDDINGS,
                file_path="results/embeddings_test.pt",
                file_size=1000,
                content_type="application/octet-stream",
                created_at=datetime.now()
            )
        ],
        error_message=None
    )
    
    # Configure the mock
    mock_workflow_service.get_workflow.return_value = mock_result

    # Test the endpoint
    response = client_with_mocks.get("/api/v1/workflows/test-id")
    
    # Assertions
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["workflow_id"] == "test-id"
    assert response_data["status"] == "completed"

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