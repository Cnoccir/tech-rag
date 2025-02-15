import os
import boto3
from botocore.exceptions import ClientError
from botocore.config import Config

class S3Manager:
    def __init__(self):
        self.bucket_name = os.getenv("AWS_BUCKET_NAME")
        if not self.bucket_name:
            raise ValueError("AWS_BUCKET_NAME must be set in .env")

        region = os.getenv("AWS_REGION", "us-east-1")
        access_key = os.getenv("AWS_ACCESS_KEY_ID")
        secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")

        config = Config(
            retries={"max_attempts": 3, "mode": "standard"},
            region_name=region
        )
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            config=config
        )

    def upload_file(self, local_path: str, s3_key: str) -> bool:
        try:
            self.s3_client.upload_file(local_path, self.bucket_name, s3_key)
            return True
        except ClientError as e:
            return False

    def download_file(self, s3_key: str, local_path: str) -> bool:
        """
        Download from S3. Returns True if success, False if error.
        """
        try:
            self.s3_client.download_file(self.bucket_name, s3_key, local_path)
            return True
        except ClientError:
            return False

    def delete_file(self, s3_key: str) -> bool:
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            return True
        except ClientError:
            return False

    def get_presigned_url(self, s3_key: str, expires_in=3600) -> str:
        """
        Generate a presigned URL for reading object from S3.
        If fails, returns empty string.
        """
        try:
            return self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": s3_key},
                ExpiresIn=expires_in
            )
        except ClientError:
            return ""
