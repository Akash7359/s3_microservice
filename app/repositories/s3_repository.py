"""
S3 Repository handles AWS S3 operations.
"""

import boto3
from app.core.config import settings


class S3Repository:
    """
    Handles file operations in S3.
    """

    def __init__(self):
        self.s3 = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY,
            aws_secret_access_key=settings.AWS_SECRET_KEY,
            region_name=settings.AWS_REGION
        )

    def upload_file(self, file_obj, bucket: str, key: str):
        self.s3.upload_fileobj(file_obj, bucket, key)

    def delete_file(self, bucket: str, key: str):
        self.s3.delete_object(Bucket=bucket, Key=key)

    def generate_signed_url(self, bucket: str, key: str):
        return self.s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=3600
        )