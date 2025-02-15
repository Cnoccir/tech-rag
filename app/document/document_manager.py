import os
from datetime import datetime
from typing import List, Optional
import uuid
import boto3
from botocore.exceptions import ClientError
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.database.models import Document as DBDocument, User, DocumentStatus, DocumentCategory
from app.schemas import Document, DocumentCreate
from app.config import get_settings

settings = get_settings()

class DocumentManager:
    def __init__(self, db: Session):
        self.db = db
        try:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
                region_name=settings.aws_region
            )
        except (ImportError, ClientError) as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to initialize S3 client: {str(e)}"
            )

    def _to_schema(self, db_document: DBDocument) -> Document:
        """Convert DB model to Pydantic schema."""
        return Document(
            id=str(db_document.id),
            filename=db_document.filename,
            file_type=db_document.file_type,
            file_size=db_document.file_size,
            s3_key=db_document.s3_key,
            status=db_document.status,
            created_at=db_document.created_at,
            updated_at=db_document.updated_at,
            created_by=str(db_document.created_by),
            category=db_document.category
        )

    def _upload_to_s3(self, file: UploadFile, s3_key: str) -> int:
        """Upload file to S3 and return file size."""
        file_content = file.file.read()
        file_size = len(file_content)
        
        self.s3_client.put_object(
            Bucket=settings.aws_bucket_name,
            Key=s3_key,
            Body=file_content
        )
        
        return file_size

    def upload_document(self, file: UploadFile, user: User, category: str = "General") -> Document:
        """Process and store a new document."""
        # Upload to S3 (sync operation)
        document_id = str(uuid.uuid4())
        s3_key = f"documents/{user.id}/{document_id}/{file.filename}"
        
        try:
            file_size = self._upload_to_s3(file, s3_key)
            
            # Create document in database
            db_document = DBDocument(
                id=document_id,
                filename=file.filename,
                s3_key=s3_key,
                created_by=user.id,
                file_type=file.content_type or "application/octet-stream",
                file_size=file_size,
                category=category,
                status=DocumentStatus.UPLOADING
            )
            
            self.db.add(db_document)
            self.db.commit()
            self.db.refresh(db_document)
            
            return self._to_schema(db_document)
            
        except Exception as e:
            # If anything fails, attempt to delete from S3 if upload succeeded
            try:
                self.s3_client.delete_object(Bucket=settings.aws_bucket_name, Key=s3_key)
            except:
                pass  # Ignore cleanup errors
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload document: {str(e)}"
            )

    def get_document_status(self, document_id: str, user: User) -> Optional[Document]:
        """Get the status of a document."""
        query = select(DBDocument).where(
            DBDocument.id == document_id,
            DBDocument.created_by == user.id
        )
        result = self.db.execute(query)
        db_document = result.scalar_one_or_none()
        
        if db_document:
            return self._to_schema(db_document)
        return None

    def list_documents(self, user: User, include_deleted: bool = False) -> List[Document]:
        """List all documents for the user."""
        query = select(DBDocument).where(DBDocument.created_by == user.id)
        if not include_deleted:
            query = query.where(DBDocument.status != DocumentStatus.DELETED)
            
        result = self.db.execute(query)
        db_documents = result.scalars().all()
        
        return [self._to_schema(doc) for doc in db_documents]

    def delete_document(self, document_id: str, user: User) -> Optional[Document]:
        """Mark a document as deleted."""
        query = select(DBDocument).where(
            DBDocument.id == document_id,
            DBDocument.created_by == user.id
        )
        result = self.db.execute(query)
        db_document = result.scalar_one_or_none()
        
        if db_document:
            db_document.status = DocumentStatus.DELETED
            db_document.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(db_document)
            return self._to_schema(db_document)
        return None
