from typing import List, Any, Optional
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Query
from sqlalchemy.orm import Session
from app.database.models import Document as DBDocument, User
from app.document.document_manager import DocumentManager
from app.routers.auth import get_current_user
from app.schemas import Document, DocumentCreate
from app.database.database import get_db
import uuid

router = APIRouter(prefix="/documents", tags=["documents"])

def convert_db_document(db_doc: DBDocument) -> Document:
    """Convert a database document model to a Pydantic schema."""
    return Document(
        id=str(db_doc.id),
        filename=db_doc.filename,
        s3_key=db_doc.s3_key,
        status=db_doc.status,
        total_chunks=db_doc.total_chunks,
        processed_chunks=db_doc.processed_chunks,
        error_message=db_doc.error_message,
        created_at=db_doc.created_at,
        updated_at=db_doc.updated_at,
        created_by=str(db_doc.created_by),
        file_type=db_doc.file_type,
        file_size=db_doc.file_size,
        category=db_doc.category
    )

@router.post("/upload", response_model=Document)
def upload_document(
    file: UploadFile = File(...),
    category: str = Query("General", enum=["Honeywell", "Tridium", "Johnson Controls", "General"]),
    db: Any = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload a new document."""
    # Initialize document manager
    doc_manager = DocumentManager(db)
    
    # Upload document using document manager
    return doc_manager.upload_document(file, current_user, category)

@router.get("/search", response_model=List[Document])
async def search_documents(
    query: str,
    category: Optional[str] = Query(None, enum=["Honeywell", "Tridium", "Johnson Controls", "General"]),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search documents using vector-based retrieval."""
    try:
        # Base query
        documents = db.query(DBDocument).filter(
            DBDocument.status != "deleted"
        )

        # Apply category filter if specified
        if category:
            documents = documents.filter(DBDocument.category == category)

        # TODO: Implement vector-based search when we add embeddings
        # For now, do simple text search on filename
        if query:
            documents = documents.filter(
                DBDocument.filename.ilike(f"%{query}%")
            )

        # Execute query and convert to list
        documents = documents.all()
        return [convert_db_document(doc) for doc in documents]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{document_id}", response_model=Document)
def get_document_status(
    document_id: str,
    db: Any = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the status of a document."""
    db_document = db.query(DBDocument).filter(DBDocument.id == document_id).first()
    if not db_document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if str(db_document.created_by) != str(current_user.id) and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to access this document")
    
    return convert_db_document(db_document)

@router.get("/list", response_model=List[Document])
def list_documents(
    include_deleted: bool = False,
    category: Optional[str] = Query(None, enum=["Honeywell", "Tridium", "Johnson Controls", "General"]),
    db: Any = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all documents."""
    query = db.query(DBDocument)
    
    if not include_deleted:
        query = query.filter(DBDocument.status != "deleted")
    
    if category:
        query = query.filter(DBDocument.category == category)
        
    if not current_user.is_admin:
        query = query.filter(DBDocument.created_by == current_user.id)
    
    db_documents = query.all()
    return [convert_db_document(doc) for doc in db_documents]

@router.delete("/{document_id}", response_model=Document)
def delete_document(
    document_id: str,
    db: Any = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark a document as deleted."""
    db_document = db.query(DBDocument).filter(DBDocument.id == document_id).first()
    if not db_document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if str(db_document.created_by) != str(current_user.id) and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to delete this document")
    
    db_document.status = "deleted"
    db.commit()
    
    return convert_db_document(db_document)
