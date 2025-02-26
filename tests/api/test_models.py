import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock
from app.models.definitions import ModelType, ModelConfig
from app.services.model_service import ModelService
from app.main import app
from app.api.routes.models import get_model_service

# Test data
mock_rna_model = ModelConfig(
    id="test-rna",
    name="Test RNA Model",
    description="Test RNA model description",
    type=ModelType.RNA,
    input_formats=["fasta"],
    version="1.0.0",
    requires_gpu=True
)

mock_dna_model = ModelConfig(
    id="test-dna",
    name="Test DNA Model",
    description="Test DNA model description",
    type=ModelType.DNA,
    input_formats=["fasta"],
    version="1.0.0",
    requires_gpu=True
)

@pytest.fixture
def mock_model_service():
    """Create a mock ModelService"""
    service = Mock(spec=ModelService)
    
    async def mock_get_available_models(model_type=None):
        if model_type == ModelType.RNA:
            return [mock_rna_model.model_dump(exclude_none=True)]
        elif model_type == ModelType.DNA:
            return [mock_dna_model.model_dump(exclude_none=True)]
        return [
            mock_rna_model.model_dump(exclude_none=True), 
            mock_dna_model.model_dump(exclude_none=True)
        ]
    
    service.get_available_models = mock_get_available_models
    return service

@pytest.fixture
def client(mock_model_service):
    """Create a test client with mocked dependencies"""
    app.dependency_overrides = {
        get_model_service: lambda: mock_model_service 
    }
    yield TestClient(app)

    # Clear overrides after test
    app.dependency_overrides.clear()

def test_get_all_models(client):
    """Test getting all models without type filter"""
    response = client.get("/api/v1/models")
    assert response.status_code == 200
    
    data = response.json()
    assert "models" in data
    assert len(data["models"]) == 2
    
    models = data["models"]
    assert any(m["type"] == ModelType.RNA for m in models)
    assert any(m["type"] == ModelType.DNA for m in models)

def test_get_rna_models(client):
    """Test getting only RNA models"""
    response = client.get("/api/v1/models", params={"model_type": "rna"})
    assert response.status_code == 200
    
    data = response.json()
    assert "models" in data
    assert len(data["models"]) == 1
    assert data["models"][0]["type"] == ModelType.RNA

def test_get_dna_models(client):
    """Test getting only DNA models"""
    response = client.get("/api/v1/models", params={"model_type": "dna"})
    assert response.status_code == 200
    
    data = response.json()
    assert "models" in data
    assert len(data["models"]) == 1
    assert data["models"][0]["type"] == ModelType.DNA

def test_invalid_model_type(client):
    """Test with invalid model type"""
    response = client.get("/api/v1/models", params={"model_type": "invalid"})
    assert response.status_code == 422  # FastAPI validation error

def test_model_structure(client):
    """Test the structure of returned model data"""
    response = client.get("/api/v1/models")
    assert response.status_code == 200
    
    data = response.json()
    model = data["models"][0]
    
    # Check required fields
    assert all(key in model for key in [
        "name",
        "type",
        "description",
        "version",
        "input_formats",
        "requires_gpu"
    ]) 