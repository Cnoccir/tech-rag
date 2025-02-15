from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
from backend.app.database.database import Base

class DocumentStatus(str, Enum):
    UPLOADING = "uploading"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DELETED = "deleted"

class DocumentCategory(str, Enum):
    HONEYWELL = "Honeywell"
    TRIDIUM = "Tridium"
    JOHNSON_CONTROLS = "Johnson Controls"
    GENERAL = "General"

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(200), nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    documents = relationship("Document", back_populates="creator")
    chats = relationship("Chat", back_populates="user")

class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True)
    filename = Column(String(255), nullable=False)
    s3_key = Column(String(255), nullable=False)
    status = Column(String(20), nullable=False, default=DocumentStatus.UPLOADING)

    # File metadata
    file_type = Column(String(100), nullable=False)
    file_size = Column(Integer, nullable=False)  # in bytes
    mime_type = Column(String(100), nullable=True)  # For more precise content type handling

    # Document categorization and description
    category = Column(SQLEnum(DocumentCategory), nullable=True, default=DocumentCategory.GENERAL)
    title = Column(String(255), nullable=True)  # Optional title different from filename
    description = Column(Text, nullable=True)  # Document description or summary
    tags = Column(Text, nullable=True)  # Comma-separated tags for additional categorization

    # Thumbnail and preview
    thumbnail_s3_key = Column(String(255), nullable=True)  # S3 key for the thumbnail image
    thumbnail_generated = Column(Boolean, default=False)  # Flag to track thumbnail generation
    preview_s3_key = Column(String(255), nullable=True)  # S3 key for a preview version (e.g., first page or excerpt)

    # Processing metadata
    total_chunks = Column(Integer, nullable=True)
    processed_chunks = Column(Integer, nullable=True)
    error_message = Column(String(500), nullable=True)
    page_count = Column(Integer, nullable=True)  # Number of pages for PDFs

    # Vector search fields
    embedding_generated = Column(Boolean, default=False)  # Flag to track embedding generation
    last_indexed_at = Column(DateTime, nullable=True)  # When the document was last indexed for search

    # Timestamps and ownership
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String, ForeignKey("users.id"))

    # Relationships
    creator = relationship("User", back_populates="documents")
    chats = relationship("Chat", back_populates="document")

class Chat(Base):
    __tablename__ = "chats"

    id = Column(String, primary_key=True)
    title = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(String, ForeignKey("users.id"))
    document_id = Column(String, ForeignKey("documents.id"))

    # Relationships
    user = relationship("User", back_populates="chats")
    document = relationship("Document", back_populates="chats")
    messages = relationship("Message", back_populates="chat")

class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True)
    chat_id = Column(String, ForeignKey('chats.id'))
    content = Column(Text, nullable=False)
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    chat = relationship("Chat", back_populates="messages")
