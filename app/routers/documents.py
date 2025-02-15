from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from app.database.database import get_db
from app.database.models import Document as DBDocument, User
from app.document.document_manager import DocumentManager
from app.routers.auth import get_current_user
from app.schemas import Document, DocumentCreate, DocumentResponse

router = APIRouter(prefix="/documents", tags=["documents"])

# Function to convert ORM model to Pydantic schema
def convert_db_document(db_doc: DBDocument) -> Document:
    return Document(
        id=str(db_doc.id),
        s3_key=db_doc.s3_key,
        filename=db_doc.filename,
        status=db_doc.status,
        file_type=db_doc.file_type,
        file_size=db_doc.file_size,
        total_chunks=db_doc.total_chunks,
        processed_chunks=db_doc.processed_chunks,
        error_message=db_doc.error_message,
        created_at=db_doc.created_at,
        updated_at=db_doc.updated_at,
        created_by=str(db_doc.created_by)
    )

@router.post("/upload", response_model=DocumentResponse)
def upload_document(
    file: UploadFile = File(...),
    db: Any = Depends(get_db),
    current_user: Any = Depends(get_current_user)
):
    """Upload a new document for processing."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can upload documents"
        )

    # Validate file type
    allowed_types = ["application/pdf", "text/plain", "application/msword",
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
    
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only PDF, TXT, DOC, and DOCX files are allowed."
        )
    
    doc_manager = DocumentManager(db)
    db_document = doc_manager.upload_document(file, current_user)

    # Convert the ORM model to a Pydantic response model
    return convert_db_document(db_document)

@router.get("/status/{document_id}", response_model=DocumentResponse)
def get_document_status(
    document_id: str,
    db: Any = Depends(get_db),
    current_user: Any = Depends(get_current_user)
):
    """Get the status of a document."""
    doc_manager = DocumentManager(db)
    db_document = doc_manager.get_document_status(document_id, current_user)
    
    if not db_document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    return convert_db_document(db_document)

@router.get("/list", response_model=List[DocumentResponse])
def list_documents(
    include_deleted: bool = False,
    db: Any = Depends(get_db),
    current_user: Any = Depends(get_current_user)
):
    """List all documents for the current user."""
    doc_manager = DocumentManager(db)
    db_documents = doc_manager.list_documents(current_user, include_deleted)

    return [convert_db_document(doc) for doc in db_documents]

@router.delete("/{document_id}", response_model=DocumentResponse)
def delete_document(
    document_id: str,
    db: Any = Depends(get_db),
    current_user: Any = Depends(get_current_user)
):
    """Delete a document and its associated data."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can delete documents"
        )

    doc_manager = DocumentManager(db)
    db_document = doc_manager.delete_document(document_id, current_user)
    
    if not db_document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    return convert_db_document(db_document)
