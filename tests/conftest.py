import sys
from unittest.mock import Mock
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.single_cell_service import get_service_instance
from app.services.workflow_service import get_workflow_service

# Create mock before any imports
mock_helical = Mock()
mock_helical.models = Mock()
mock_helical.models.scgpt = Mock()
mock_helical.models.scgpt.model = Mock()
mock_helical.models.scgpt.model.scGPT = Mock()
mock_helical.models.scgpt.model.scGPTConfig = Mock()
mock_helical.models.geneformer = Mock()
mock_helical.models.geneformer.model = Mock()
mock_helical.models.geneformer.model.Geneformer = Mock()
mock_helical.models.geneformer.model.GeneformerConfig = Mock()

# Mock helical immediately
sys.modules['helical'] = mock_helical
sys.modules['helical.models'] = mock_helical.models
sys.modules['helical.models.scgpt'] = mock_helical.models.scgpt
sys.modules['helical.models.scgpt.model'] = mock_helical.models.scgpt.model
sys.modules['helical.models.geneformer'] = mock_helical.models.geneformer
sys.modules['helical.models.geneformer.model'] = mock_helical.models.geneformer.model

@pytest.fixture(scope="session")
def mock_helical_fixture():
    """Provide the mock helical to tests if needed"""
    return mock_helical 

@pytest.fixture
def client():
    """Return a test client without mocks"""
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture
def mock_single_cell_service():
    mock = Mock()
    # Add the required methods to the mock
    mock.process_workflow = Mock()
    return mock

@pytest.fixture
def mock_workflow_service():
    mock = Mock()
    # Add all required methods
    mock.get_workflow_status = Mock()
    mock.get_workflow = Mock()
    mock.create_single_cell_workflow = Mock()
    mock.get_workflows = Mock(return_value=[])
    return mock

@pytest.fixture
def client_with_mocks(mock_single_cell_service, mock_workflow_service):
    """Return a test client with service mocks injected"""
    # Store original overrides
    original_overrides = app.dependency_overrides.copy()
    
    # Set up dependency overrides for both services
    app.dependency_overrides[get_service_instance] = lambda: mock_single_cell_service
    app.dependency_overrides[get_workflow_service] = lambda: mock_workflow_service
    
    # Create and return the client
    with TestClient(app) as test_client:
        yield test_client
    
    # Restore original dependency overrides
    app.dependency_overrides = original_overrides 