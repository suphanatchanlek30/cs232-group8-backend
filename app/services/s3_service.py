import logging
import uuid
from datetime import datetime
from typing import Optional

import boto3
from botocore.exceptions import ClientError
from fastapi import UploadFile

from app.core.config import settings

logger = logging.getLogger(__name__)

class S3Service:
    def __init__(self):
        self.bucket_name = settings.S3_BUCKET_NAME
        self.region = settings.AWS_REGION
        self.s3_client = None
        if self.bucket_name:
            self.s3_client = boto3.client("s3", region_name=self.region)

    def _get_extension(self, filename: str, mime_type: str) -> str:
        if filename and "." in filename:
            return filename.rsplit(".", 1)[-1].lower()
        mapping = {
            "image/jpeg": "jpg",
            "image/png": "png",
            "image/webp": "webp",
            "audio/mpeg": "mp3",
            "audio/mp4": "m4a",
            "video/mp4": "mp4",
        }
        return mapping.get(mime_type, "bin")

    def upload_file(self, file: UploadFile, user_id: str) -> Optional[dict]:
        """
        Uploads a file to S3 and returns a dictionary with url and key.
        Directory structure: uploads/{YYYY}/{MM}/{DD}/{user_id}/{uuid}.{ext}
        """
        if not self.s3_client or not self.bucket_name:
            logger.warning("S3_BUCKET_NAME is not configured. Skipping S3 upload.")
            return None

        try:
            now = datetime.utcnow()
            file_bytes = file.file.read()
            mime_type = file.content_type or "application/octet-stream"
            ext = self._get_extension(file.filename, mime_type)
            
            key = f"uploads/{now.strftime('%Y/%m/%d')}/{user_id}/{uuid.uuid4().hex}.{ext}"
            
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=file_bytes,
                ContentType=mime_type,
            )
            
            file_url = f"https://{self.bucket_name}.s3.amazonaws.com/{key}"
            
            return {
                "file_url": file_url,
                "file_key": key,
                "file_type": "IMAGE" if mime_type.startswith("image/") else "AUDIO" if mime_type.startswith("audio/") else "FILE",
                "mime_type": mime_type,
                "file_size_bytes": len(file_bytes)
            }
        except ClientError as e:
            logger.error(f"Failed to upload to S3: {e}")
            return None
        finally:
            file.file.seek(0)

s3_service = S3Service()