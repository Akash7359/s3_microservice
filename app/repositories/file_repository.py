"""
Database repository.
"""

from sqlalchemy.orm import Session
from app.models.file_model import File


class FileRepository:

    def __init__(self, db: Session):
        self.db = db

    def create(self, file: File):
        self.db.add(file)
        self.db.commit()
        self.db.refresh(file)
        return file

    def get(self, file_id: str):
        return self.db.query(File).filter(
            File.id == file_id,
            File.is_deleted == False
        ).first()

    def soft_delete(self, file: File):
        file.is_deleted = True
        self.db.commit()