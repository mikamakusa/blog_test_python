from minio import Minio
from minio.error import S3Error
import logging
from config import settings
from io import BytesIO

logger = logging.getLogger(__name__)

class MinioClient:
    def __init__(self):
        self.client = Minio(
            f"{settings.minio_host}:{settings.minio_port}",
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure
        )
        self.bucket_name = settings.minio_bucket
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """Ensure the bucket exists, create if it doesn't."""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info(f"Created bucket: {self.bucket_name}")
        except S3Error as e:
            logger.error(f"Error ensuring bucket exists: {e}")
            raise e
    
    async def upload_file(self, file_data: bytes, filename: str, folder: str, content_type: str):
        """Upload a file to MinIO."""
        try:
            object_name = f"{folder}/{filename}"
            
            # Convert bytes to file-like object
            file_stream = BytesIO(file_data)
            
            self.client.put_object(
                self.bucket_name,
                object_name,
                file_stream,
                length=len(file_data),
                content_type=content_type
            )
            return object_name
        except S3Error as e:
            logger.error(f"Error uploading file: {e}")
            raise e
    
    async def delete_file(self, object_name: str):
        """Delete a file from MinIO."""
        try:
            self.client.remove_object(self.bucket_name, object_name)
            return True
        except S3Error as e:
            logger.error(f"Error deleting file: {e}")
            raise e
    
    def get_file_url(self, object_name: str, expires: int = 3600):
        """Get a presigned URL for a file."""
        try:
            return self.client.presigned_get_object(
                self.bucket_name,
                object_name,
                expires=expires
            )
        except S3Error as e:
            logger.error(f"Error getting file URL: {e}")
            raise e
    
    async def list_files(self, folder: str = None):
        """List files in a folder."""
        try:
            prefix = f"{folder}/" if folder else ""
            objects = self.client.list_objects(self.bucket_name, prefix=prefix, recursive=True)
            return [obj.object_name for obj in objects]
        except S3Error as e:
            logger.error(f"Error listing files: {e}")
            raise e

minio_client = MinioClient() 