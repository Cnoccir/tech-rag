import boto3
import os
import tempfile
import uuid
from botocore.config import Config
from botocore.exceptions import ClientError
import logging
from typing import Optional, Tuple, Dict
from pathlib import Path

logger = logging.getLogger(__name__)

class S3Manager:
    def __init__(self):
        self.s3_client = self._get_s3_client()
        self.bucket_name = os.getenv('AWS_BUCKET_NAME')
        if not self.bucket_name:
            raise ValueError("AWS_BUCKET_NAME environment variable is not set")

    def _get_s3_client(self):
        """Initialize and return an S3 client."""
        try:
            config = Config(
                retries={'max_attempts': 3, 'mode': 'standard'},
                region_name=os.getenv('AWS_REGION')
            )

            return boto3.client('s3',
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                config=config
            )
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {str(e)}")
            raise

    def generate_s3_key(self, doc_id: str, file_type: str = 'pdf') -> str:
        """Generate an S3 key for a document."""
        return f"{doc_id}.{file_type}"

    def upload_file(self, local_file_path: str, doc_id: Optional[str] = None) -> Tuple[Dict[str, str], int]:
        """Upload a file to S3."""
        if doc_id is None:
            doc_id = str(uuid.uuid4())
        
        s3_key = self.generate_s3_key(doc_id)
        try:
            self.s3_client.upload_file(local_file_path, self.bucket_name, s3_key)
            logger.info(f"Successfully uploaded file to S3 with key: {s3_key}")
            return {"doc_id": doc_id}, 200
        except ClientError as e:
            logger.error(f"Error uploading file: {str(e)}")
            return {"error": str(e)}, 500

    def download_file(self, doc_id: str) -> Optional[str]:
        """Download a file from S3 to a temporary location."""
        s3_key = self.generate_s3_key(doc_id)
        temp_dir = tempfile.TemporaryDirectory()
        local_path = Path(temp_dir.name) / s3_key

        try:
            self.s3_client.download_file(self.bucket_name, s3_key, str(local_path))
            return str(local_path)
        except ClientError as e:
            logger.error(f"Error downloading file {doc_id}: {str(e)}")
            temp_dir.cleanup()
            return None

    def delete_file(self, doc_id: str) -> Tuple[Dict[str, str], int]:
        """Delete a file from S3."""
        s3_key = self.generate_s3_key(doc_id)
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            return {"message": f"Successfully deleted {doc_id}"}, 200
        except ClientError as e:
            logger.error(f"Error deleting file {doc_id}: {str(e)}")
            return {"error": str(e)}, 500

    def get_download_url(self, doc_id: str, expires_in: int = 3600) -> Optional[str]:
        """Generate a presigned URL for downloading a file."""
        s3_key = self.generate_s3_key(doc_id)
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': s3_key},
                ExpiresIn=expires_in
            )
            return url
        except ClientError as e:
            logger.error(f"Error generating presigned URL for {doc_id}: {str(e)}")
            return None
