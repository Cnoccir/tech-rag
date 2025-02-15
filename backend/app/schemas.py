from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from backend.app.database.models import DocumentCategory

class Token(BaseModel):
    access_token: str
    token_type: str

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str
    is_admin: bool = False

class User(UserBase):
    id: str
    is_admin: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class DocumentBase(BaseModel):
    filename: str
    file_type: str
    file_size: int
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[str] = None
    category: DocumentCategory = DocumentCategory.GENERAL

class DocumentCreate(DocumentBase):
    s3_key: str
    created_by: str
    mime_type: Optional[str] = None

class Document(DocumentBase):
    id: str
    s3_key: str
    status: str
    mime_type: Optional[str] = None

    # Thumbnail and preview
    thumbnail_s3_key: Optional[str] = None
    thumbnail_generated: bool = False
    preview_s3_key: Optional[str] = None

    # Processing metadata
    total_chunks: Optional[int] = None
    processed_chunks: Optional[int] = None
    error_message: Optional[str] = None
    page_count: Optional[int] = None

    # Vector search fields
    embedding_generated: bool = False
    last_indexed_at: Optional[datetime] = None

    # Timestamps and ownership
    created_at: datetime
    updated_at: datetime
    created_by: str

    model_config = ConfigDict(from_attributes=True)

class ChatBase(BaseModel):
    title: str

class ChatCreate(ChatBase):
    document_id: str

class Chat(ChatBase):
    id: str
    created_at: datetime
    user_id: str
    document_id: str
    model_config = ConfigDict(from_attributes=True)

class MessageBase(BaseModel):
    content: str
    role: str

class MessageCreate(MessageBase):
    chat_id: str

class Message(MessageBase):
    id: str
    chat_id: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
