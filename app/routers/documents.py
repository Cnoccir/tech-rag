from typing import List, Optional
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.database.models import Document as DBDocument, User
from app.routers.auth import get_current_user
from app.schemas import Document
from app.document.document_manager import DocumentManager
from app.document.s3_manager import S3Manager

router = APIRouter(prefix="/documents", tags=["documents"])

def convert_db_document(db_doc: DBDocument) -> Document:
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

@router.post("/upload", response_model=Document)
def upload_document(
    file: UploadFile = File(...),
    category: str = Query("General", enum=["Honeywell", "Tridium", "Johnson Controls", "General"]),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload a new document + run docling processing + embedding (synchronous).
    """
    doc_manager = DocumentManager(db)
    doc_schema = doc_manager.upload_document(file, current_user, category)
    return doc_schema

@router.get("/list", response_model=List[Document])
def list_documents(
    include_deleted: bool = False,
    category: Optional[str] = Query(None, enum=["Honeywell", "Tridium", "Johnson Controls", "General"]),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all documents. Non-admin sees only their docs. Admin sees everything.
    """
    doc_manager = DocumentManager(db)
    docs = doc_manager.list_documents(user=current_user, include_deleted=include_deleted)
    if category:
        docs = [d for d in docs if d.category == category]
    return docs

@router.delete("/{document_id}", response_model=Document)
def delete_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Mark a document as DELETED. Only the owner or admin can do this.
    """
    doc_manager = DocumentManager(db)
    deleted_doc = doc_manager.delete_document(document_id, current_user)
    if not deleted_doc:
        raise HTTPException(status_code=404, detail="Document not found or not authorized.")
    return deleted_doc

@router.get("/search", response_model=List[Document])
def search_documents(
    query: str,
    category: Optional[str] = Query(None, enum=["Honeywell", "Tridium", "Johnson Controls", "General"]),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    A placeholder search that does *not* do vector-based search yet.
    If you want vector-based search, you can do that in docling_processor or a separate route.
    For now, this route matches your original approach (filename contains query).
    """
    q = db.query(DBDocument).filter(DBDocument.status != "deleted")
    if not current_user.is_admin:
        q = q.filter(DBDocument.created_by == current_user.id)
    if category:
        q = q.filter(DBDocument.category == category)

    if query:
        q = q.filter(DBDocument.filename.ilike(f"%{query}%"))

    db_docs = q.all()
    return [convert_db_document(d) for d in db_docs]

@router.get("/{document_id}/download_url")
def get_document_download_url(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Return a presigned S3 URL so the user can view the PDF in the streamlit-pdf-viewer.
    """
    doc = db.query(DBDocument).filter(DBDocument.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.created_by != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")

    s3_mgr = S3Manager()
    url = s3_mgr.get_presigned_url(doc.s3_key, expires_in=3600)
    if not url:
        raise HTTPException(status_code=500, detail="Failed to generate presigned URL")
    return {"url": url}
