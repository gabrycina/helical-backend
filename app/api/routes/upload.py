from fastapi import APIRouter, UploadFile, File, HTTPException
from app.core.config import get_settings
import shutil
from pathlib import Path

router = APIRouter()
settings = get_settings()

def validate_file_extension(filename: str) -> bool:
    return filename.split(".")[-1].lower() in settings.ALLOWED_EXTENSIONS

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)) -> dict:
    """
    Upload a file for processing
    """
    if not validate_file_extension(file.filename):
        raise HTTPException(
            status_code=400,
            detail=f"File extension not allowed. Must be one of: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )
    
    try:
        file_path = settings.UPLOAD_DIR / file.filename
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        return {
            "filename": file.filename,
            "path": str(file_path),
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 