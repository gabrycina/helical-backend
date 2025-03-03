from functools import lru_cache
from pathlib import Path
from typing import Set
from pydantic import ConfigDict
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env")
    
    # API Config
    APP_NAME: str = "Helical Workflow API"
    DEBUG: bool = False
    API_V1_STR: str = "/api/v1"
    
    # File handling
    UPLOAD_DIR: Path = Path("uploads")
    RESULTS_DIR: Path = UPLOAD_DIR / "results"
    MAX_UPLOAD_SIZE: int = 500_000_000  # 500MB
    ALLOWED_EXTENSIONS: Set[str] = {
        "fasta", "fa",  # FASTA format (header + sequence)
        "pdb",          # Protein structure data
        "txt",          # Raw sequence data
        "csv", "tsv",    # Expression/tabular data
        "h5ad"
    }

@lru_cache()
def get_settings() -> Settings:
    settings = Settings()
    
    # Ensure directories exist
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    settings.RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    return settings 