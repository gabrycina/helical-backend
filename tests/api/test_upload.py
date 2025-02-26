import pytest
from fastapi.testclient import TestClient
from pathlib import Path
from app.main import app
from app.core.config import get_settings

settings = get_settings()

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def sample_fasta_content():
    return b">sequence1\nATGCATGC\n>sequence2\nGCATGCAT"

@pytest.fixture
def sample_txt_content():
    return b"ATGCATGCGCATGCAT"

def test_upload_valid_fasta(client, sample_fasta_content):
    """Test uploading a valid FASTA file"""
    files = {"file": ("test.fasta", sample_fasta_content, "text/plain")}
    response = client.post("/api/v1/upload", files=files)
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["filename"] == "test.fasta"
    assert Path(data["path"]).exists()
    
    # Cleanup
    Path(data["path"]).unlink()

def test_upload_valid_txt(client, sample_txt_content):
    """Test uploading a valid TXT file"""
    files = {"file": ("sequence.txt", sample_txt_content, "text/plain")}
    response = client.post("/api/v1/upload", files=files)
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["filename"] == "sequence.txt"
    assert Path(data["path"]).exists()
    
    Path(data["path"]).unlink()

def test_upload_invalid_extension(client, sample_fasta_content):
    """Test uploading a file with invalid extension"""
    files = {"file": ("test.invalid", sample_fasta_content, "text/plain")}
    response = client.post("/api/v1/upload", files=files)
    
    assert response.status_code == 400
    assert "extension not allowed" in response.json()["detail"]

def test_upload_empty_file(client):
    """Test uploading an empty file"""
    files = {"file": ("empty.fasta", b"", "text/plain")}
    response = client.post("/api/v1/upload", files=files)
    
    assert response.status_code == 200 
    data = response.json()
    assert data["status"] == "success"
    
    Path(data["path"]).unlink()

@pytest.mark.parametrize("filename", [
    "test.fasta",
    "test.fa",
    "test.txt",
    "test.csv",
    "test.tsv",
    "test.pdb"
])
def test_all_allowed_extensions(client, filename):
    """Test all allowed file extensions"""
    content = b"some content"
    files = {"file": (filename, content, "text/plain")}
    response = client.post("/api/v1/upload", files=files)
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    
    Path(data["path"]).unlink() 