"""
API Layer (Router)
"""

from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.services.file_service import FileService
from app.schemas.file_schema import FileResponse

router = APIRouter(prefix="/api/v1/files", tags=["Files"])


@router.post("/upload", response_model=FileResponse)
async def upload_file(
    user_id: int,
    module_name: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    service = FileService(db)
    return service.upload_file(file, user_id, module_name)