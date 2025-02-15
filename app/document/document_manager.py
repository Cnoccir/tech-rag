import os
from datetime import datetime
from typing import List, Optional
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.database.models import Document as DBDocument, User, DocumentStatus
from app.schemas import Document as DocumentSchema, DocumentCreate
from app.config import get_settings

settings = get_settings()

class DocumentManager:
    def __init__(self, db: Session):
        self.db = db
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.aws_region
        )

    def _to_schema(self, document: DBDocument) -> DocumentSchema:
        """Convert SQLAlchemy model to Pydantic schema."""
        return DocumentSchema(
            id=str(document.id),
            s3_key=document.s3_key,
            filename=document.filename,
            status=document.status.value,
            file_type=document.file_type,
            file_size=document.file_size,
            total_chunks=document.total_chunks,
            processed_chunks=document.processed_chunks,
            error_message=document.error_message,
            created_at=document.created_at,
            updated_at=document.updated_at,
            created_by=str(document.created_by)
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

    def upload_document(self, file: UploadFile, user: User) -> DocumentSchema:
        """Upload a document and start processing."""
        document_id = str(uuid.uuid4())
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else ''
        s3_key = f"documents/{document_id}.{file_extension}"
        
        # Upload to S3 (sync operation)
        file_size = self._upload_to_s3(file, s3_key)
        
        # Create document record
        document = DBDocument(
            id=document_id,
            s3_key=s3_key,
            filename=file.filename,
            status=DocumentStatus.PENDING,
            file_type=file.content_type,
            file_size=file_size,
            created_by=user.id
        )
        
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        
        # Start async processing
        # TODO: Implement background task for processing
        
        return self._to_schema(document)

    def get_document_status(self, document_id: str, user: User) -> Optional[DocumentSchema]:
        """Get the status of a document."""
        query = select(DBDocument).where(
            DBDocument.id == document_id,
            DBDocument.created_by == user.id
        )
        result = self.db.execute(query)
        document = result.scalar_one_or_none()
        
        if document:
            return self._to_schema(document)
        return None

    def list_documents(self, user: User, include_deleted: bool = False) -> List[DocumentSchema]:
        """List all documents for the user."""
        query = select(DBDocument).where(DBDocument.created_by == user.id)
        if not include_deleted:
            query = query.where(DBDocument.status != DocumentStatus.DELETED)
            
        result = self.db.execute(query)
        documents = result.scalars().all()
        
        return [self._to_schema(doc) for doc in documents]

    def delete_document(self, document_id: str, user: User) -> Optional[DocumentSchema]:
        """Mark a document as deleted."""
        query = select(DBDocument).where(
            DBDocument.id == document_id,
            DBDocument.created_by == user.id
        )
        result = self.db.execute(query)
        document = result.scalar_one_or_none()
        
        if document:
            document.status = DocumentStatus.DELETED
            document.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(document)
            return self._to_schema(document)
        return None
