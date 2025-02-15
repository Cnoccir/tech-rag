# app/routers/documents.py
from typing import List, Optional
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Query, status
from sqlalchemy.orm import Session
import logging

from backend.app.database.database import get_db
from backend.app.database.models import Document as DBDocument, User, DocumentStatus
from backend.app.routers.auth import get_current_user
from backend.app.schemas import Document
from backend.app.document.document_manager import DocumentManager
from backend.app.document.s3_manager import S3Manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/documents", tags=["documents"])

def convert_db_document(db_doc: DBDocument) -> Document:
    """Convert database model to schema model"""
    try:
        return Document(
            id=db_doc.id,
            filename=db_doc.filename,
            s3_key=db_doc.s3_key,
            status=db_doc.status,
            total_chunks=db_doc.total_chunks,
            processed_chunks=db_doc.processed_chunks,
            error_message=db_doc.error_message,
            created_at=db_doc.created_at,
            updated_at=db_doc.updated_at,
            created_by=db_doc.created_by,
            file_type=db_doc.file_type,
            file_size=db_doc.file_size,
            category=db_doc.category
        )
    except Exception as e:
        logger.error(f"Error converting document model: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing document data"
        )

@router.get("/list", response_model=List[Document])
async def list_documents(
    include_deleted: bool = False,
    category: Optional[str] = Query(None, enum=["Honeywell", "Tridium", "Johnson Controls", "General"]),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List documents with optional filters"""
    try:
        logger.debug(f"Listing documents for user {current_user.username} (admin: {current_user.is_admin})")
        query = db.query(DBDocument)

        # Filter by deletion status
        if not include_deleted:
            query = query.filter(DBDocument.status != DocumentStatus.DELETED)

        # Filter by user access
        if not current_user.is_admin:
            query = query.filter(DBDocument.created_by == current_user.id)

        # Filter by category if specified
        if category:
            query = query.filter(DBDocument.category == category)

        # Execute query
        db_docs = query.all()
        logger.debug(f"Found {len(db_docs)} documents matching criteria")

        # Convert to response model
        return [convert_db_document(doc) for doc in db_docs]

    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving documents: {str(e)}"
        )

@router.post("/upload", response_model=Document)
async def upload_document(
    file: UploadFile = File(...),
    category: str = Query("General", enum=["Honeywell", "Tridium", "Johnson Controls", "General"]),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload and process a new document"""
    try:
        logger.info(f"Processing upload request for {file.filename} from user {current_user.username}")
        doc_manager = DocumentManager(db)
        doc_schema = doc_manager.upload_document(file, current_user, category)
        return doc_schema

    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading document: {str(e)}"
        )

@router.get("/{document_id}/download_url")
async def get_document_download_url(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns a presigned URL for this document's S3 object, if the user owns it or is admin.
    """
    doc = db.query(DBDocument).filter(DBDocument.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.created_by != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")

    s3_manager = S3Manager()
    presigned_url = s3_manager.get_presigned_url(doc.s3_key)
    if not presigned_url:
        raise HTTPException(status_code=500, detail="Failed to generate presigned URL")

    return {"url": presigned_url}
    
@router.delete("/{document_id}", response_model=Document)
async def delete_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark a document as deleted"""
    try:
        doc_manager = DocumentManager(db)
        deleted_doc = doc_manager.delete_document(document_id, current_user)
        if not deleted_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found or not authorized"
            )
        return deleted_doc

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document {document_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting document: {str(e)}"
        )

@router.get("/search", response_model=List[Document])
async def search_documents(
    query: str,
    category: Optional[str] = Query(None, enum=["Honeywell", "Tridium", "Johnson Controls", "General"]),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search documents with vector-based retrieval"""
    try:
        # Build base query
        q = db.query(DBDocument).filter(DBDocument.status != DocumentStatus.DELETED)

        # Apply access control
        if not current_user.is_admin:
            q = q.filter(DBDocument.created_by == current_user.id)

        # Apply category filter
        if category:
            q = q.filter(DBDocument.category == category)

        # Apply search filter
        if query:
            q = q.filter(DBDocument.filename.ilike(f"%{query}%"))

        db_docs = q.all()
        return [convert_db_document(d) for d in db_docs]

    except Exception as e:
        logger.error(f"Error searching documents: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching documents: {str(e)}"
        )
