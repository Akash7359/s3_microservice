"""
Business Logic Layer
"""

import os
import datetime
from app.repositories.s3_repository import S3Repository
from app.repositories.file_repository import FileRepository
from app.models.file_model import File
from app.core.config import settings


class FileService:

    def __init__(self, db):
        self.db_repo = FileRepository(db)
        self.s3_repo = S3Repository()

    def upload_file(self, file, user_id: int, module_name: str):

        # Validate size
        file.file.seek(0, os.SEEK_END)
        size = file.file.tell()

        if size > settings.MAX_FILE_SIZE:
            raise Exception("File too large")

        file.file.seek(0)

        extension = file.filename.split(".")[-1]

        now = datetime.datetime.utcnow()
        key = f"S3_service/{now.year}/{now.strftime('%B')}/{user_id}/{module_name}/{file.filename}"

        # Upload to S3
        self.s3_repo.upload_file(file.file, settings.AWS_BUCKET, key)

        # Save metadata
        file_obj = File(
            user_id=user_id,
            module_name=module_name,
            original_filename=file.filename,
            stored_filename=file.filename,
            file_extension=extension,
            file_size=size,
            s3_path=key,
            bucket_name=settings.AWS_BUCKET
        )

        return self.db_repo.create(file_obj)