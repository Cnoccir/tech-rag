import uuid
import os
from datetime import datetime
from typing import List, Optional
import boto3
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.database.models import Document as DBDocument, User, DocumentStatus, DocumentCategory
from app.schemas import Document, DocumentCreate
from app.config import get_settings
from app.document.s3_manager import S3Manager
from app.document.docling_processor import DoclingProcessor

settings = get_settings()

class DocumentManager:
    def __init__(self, db: Session):
        self.db = db
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.aws_region
        )
        self.bucket_name = settings.aws_bucket_name
        self.docling_processor = DoclingProcessor()

    def _to_schema(self, db_document: DBDocument) -> Document:
        return Document(
            id=db_document.id,
            filename=db_document.filename,
            s3_key=db_document.s3_key,
            status=db_document.status,
            created_at=db_document.created_at,
            updated_at=db_document.updated_at,
            created_by=db_document.created_by,
            file_type=db_document.file_type,
            file_size=db_document.file_size,
            category=db_document.category
        )

    def upload_document(self, file: UploadFile, user: User, category: str = "General") -> Document:
        """
        1) Generate doc_id
        2) Upload file to S3
        3) Create Document in DB (status=UPLOADING)
        4) Trigger docling processing + embedding (async or sync)
        """
        document_id = str(uuid.uuid4())
        s3_key = f"documents/{user.id}/{document_id}/{file.filename}"

        try:
            file_bytes = file.file.read()
            file_size = len(file_bytes)

            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_bytes
            )

            # Create DB record
            db_document = DBDocument(
                id=document_id,
                filename=file.filename,
                s3_key=s3_key,
                status=DocumentStatus.UPLOADING,
                created_by=user.id,
                file_type=file.content_type or "application/octet-stream",
                file_size=file_size,
                category=category
            )
            self.db.add(db_document)
            self.db.commit()
            self.db.refresh(db_document)

            # [Optional] Immediately run docling + pinecone indexing
            # You could also run this in a background task (Celery, RQ, etc.)
            db_document.status = DocumentStatus.PROCESSING
            self.db.commit()
            meta_dict = {
                "uploaded_by": user.username,
                "category": category,
            }
            process_result = self.docling_processor.process_and_index_document(
                document_id=document_id,
                s3_key=s3_key,
                metadata=meta_dict
            )
            if process_result["status"] == "success":
                db_document.status = DocumentStatus.COMPLETED
            else:
                db_document.status = DocumentStatus.FAILED
                db_document.error_message = process_result.get("error", "")
            db_document.updated_at = datetime.utcnow()
            self.db.commit()

            return self._to_schema(db_document)

        except Exception as e:
            # Cleanup if something fails
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )

    def list_documents(self, user: User, include_deleted=False) -> List[Document]:
        query = self.db.query(DBDocument)
        if not include_deleted:
            query = query.filter(DBDocument.status != DocumentStatus.DELETED)
        # Non-admin sees only their docs
        if not user.is_admin:
            query = query.filter(DBDocument.created_by == user.id)
        docs = query.all()
        return [self._to_schema(d) for d in docs]

    def delete_document(self, document_id: str, user: User) -> Optional[Document]:
        db_document = self.db.query(DBDocument).filter(DBDocument.id == document_id).first()
        if not db_document:
            return None
        # check ownership or admin
        if db_document.created_by != user.id and not user.is_admin:
            return None

        db_document.status = DocumentStatus.DELETED
        db_document.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(db_document)
        return self._to_schema(db_document)

    def get_document_status(self, document_id: str, user: User) -> Optional[Document]:
        db_document = self.db.query(DBDocument).filter(DBDocument.id == document_id).first()
        if not db_document:
            return None
        # ownership check
        if db_document.created_by != user.id and not user.is_admin:
            return None
        return self._to_schema(db_document)
