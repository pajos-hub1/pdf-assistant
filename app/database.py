from sqlalchemy import (
    create_engine, Column, String, Boolean,
    DateTime, Text, Integer, ForeignKey
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import uuid
import os

# Database URL — SQLite for development, swap to PostgreSQL in production
# PostgreSQL example: "postgresql://user:password@localhost/dbname"
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/pdf_assistant.db")

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # needed for SQLite only
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all models
Base = declarative_base()


# ─────────────────────────────────────────
# MODELS
# ─────────────────────────────────────────

class APIKey(Base):
    """Stores API keys and their owners."""
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True, nullable=False)
    owner_name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # One API key → many sessions
    sessions = relationship("Session", back_populates="api_key")


class Session(Base):
    """One session per user per conversation."""
    __tablename__ = "sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    api_key_id = Column(Integer, ForeignKey("api_keys.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    api_key = relationship("APIKey", back_populates="sessions")
    chat_history = relationship("ChatHistory", back_populates="session")
    documents = relationship("Document", back_populates="session")


class ChatHistory(Base):
    """Stores every question and answer per session."""
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    language = Column(String, default="English")
    confidence = Column(String, default="0%")
    sources = Column(String, default="")
    suggestions = Column(Text, default="")  # stored as pipe-separated string
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    session = relationship("Session", back_populates="chat_history")


class Document(Base):
    """Tracks uploaded PDFs per session."""
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    summary = Column(Text, default="")
    status = Column(String, default="processing")  # processing | done | failed
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    session = relationship("Session", back_populates="documents")


# ─────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────

def get_db():
    """Dependency — yields a DB session and closes it after use."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables if they don't exist."""
    os.makedirs("data", exist_ok=True)
    Base.metadata.create_all(bind=engine)
    print("Database initialized")


def create_api_key(owner_name: str, key: str = None) -> str:
    """
    Helper to create a new API key.
    Call this manually to generate keys for users.
    """
    db = SessionLocal()
    try:
        # Auto-generate key if not provided
        if not key:
            key = f"sk-{uuid.uuid4().hex[:32]}"

        api_key = APIKey(key=key, owner_name=owner_name)
        db.add(api_key)
        db.commit()
        db.refresh(api_key)
        print(f"API key created for {owner_name}: {key}")
        return key
    finally:
        db.close()


def get_or_create_session(db, api_key_id: int, session_id: str = None) -> Session:
    """Get existing session or create a new one."""
    if session_id:
        session = db.query(Session).filter(Session.id == session_id).first()
        if session:
            session.last_active = datetime.utcnow
            db.commit()
            return session

    # Create new session
    session = Session(api_key_id=api_key_id)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def save_chat(
    db,
    session_id: str,
    question: str,
    answer: str,
    language: str,
    confidence: str,
    sources: list,
    suggestions: list
):
    """Save a Q&A exchange to the database."""
    chat = ChatHistory(
        session_id=session_id,
        question=question,
        answer=answer,
        language=language,
        confidence=confidence,
        sources=str(sources),
        suggestions="|".join(suggestions)  # pipe-separated
    )
    db.add(chat)
    db.commit()
    db.refresh(chat)
    return chat


def save_document(db, session_id: str, filename: str, file_path: str) -> Document:
    """Save uploaded document record to DB with status=processing."""
    doc = Document(
        session_id=session_id,
        filename=filename,
        file_path=file_path,
        status="processing"
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def update_document_status(db, doc_id: int, status: str, summary: str = ""):
    """Update document status after OCR/ingestion completes."""
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if doc:
        doc.status = status
        doc.summary = summary
        db.commit()
    return doc