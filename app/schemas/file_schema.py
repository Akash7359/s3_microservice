"""
Pydantic schemas.
Used for request & response validation.
"""

from pydantic import BaseModel
from datetime import datetime


class FileResponse(BaseModel):
    id: str
    user_id: int
    module_name: str
    original_filename: str
    s3_path: str
    created_at: datetime

    class Config:
        from_attributes = True