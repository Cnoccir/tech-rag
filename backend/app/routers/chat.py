from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Any, List, Dict
from backend.app.database.database import get_db
from backend.app.routers.auth import get_current_user
from sqlalchemy.orm import Session
from backend.app.database.models import Document as DBDocument
from backend.app.chat.chat_manager import ChatManager

router = APIRouter(prefix="/chat", tags=["chat"])

class ChatRequest(BaseModel):
    document_id: str
    query: str
    history: List[Dict[str, str]] = []

@router.post("/ask")
def ask_chat(
    req: ChatRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
) -> Any:
    """
    Example RAG-based chat endpoint.
    We only allow the user if they own the doc or are admin.
    Then we do doc-based retrieval from Pinecone, pass it to an LLM, etc.
    """
    doc = db.query(DBDocument).filter(DBDocument.id == req.document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.created_by != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")

    # You can pass [req.document_id] as the single doc to ChatManager or multiple
    chat_manager = ChatManager()
    res = chat_manager.generate_response(
        query=req.query,
        document_ids=[req.document_id],
        chat_history=req.history
    )
    return {
        "response": res["response"],
        "citations": res["citations"]
    }
