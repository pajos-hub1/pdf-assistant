from sqlalchemy import (
    create_engine, Column, String, Boolean,
    DateTime, Text, Integer, ForeignKey
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from passlib.context import CryptContext
import uuid
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/pdf_assistant.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Password hashing
pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
    argon2__memory_cost=65536,  # 64MB memory — hard to brute force
    argon2__time_cost=3,        # 3 iterations
    argon2__parallelism=4       # 4 parallel threads
)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ─────────────────────────────────────────
# MODELS
# ─────────────────────────────────────────

class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True, nullable=False)
    owner_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    sessions = relationship("Session", back_populates="api_key")


class Session(Base):
    __tablename__ = "sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    api_key_id = Column(Integer, ForeignKey("api_keys.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)

    api_key = relationship("APIKey", back_populates="sessions")
    chat_history = relationship("ChatHistory", back_populates="session")
    documents = relationship("Document", back_populates="session")


class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    language = Column(String, default="English")
    confidence = Column(String, default="0%")
    sources = Column(String, default="")
    suggestions = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("Session", back_populates="chat_history")


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    summary = Column(Text, default="")
    status = Column(String, default="processing")
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("Session", back_populates="documents")


# ─────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    os.makedirs("data", exist_ok=True)
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized")


def register_user(owner_name: str, email: str, password: str) -> dict:
    """Register a new user — returns api_key or error."""
    db = SessionLocal()
    try:
        # Check if email already exists
        existing = db.query(APIKey).filter(APIKey.email == email).first()
        if existing:
            return {"error": "Email already registered. Please login instead."}

        key = f"sk-{uuid.uuid4().hex[:32]}"
        user = APIKey(
            key=key,
            owner_name=owner_name,
            email=email,
            hashed_password=hash_password(password)
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"✅ User registered: {email}")
        return {"api_key": key, "owner": owner_name, "email": email}
    finally:
        db.close()


def login_user(email: str, password: str) -> dict:
    """Login user — returns api_key or error."""
    db = SessionLocal()
    try:
        user = db.query(APIKey).filter(APIKey.email == email).first()
        if not user:
            return {"error": "Email not found. Please register first."}
        if not verify_password(password, user.hashed_password):
            return {"error": "Incorrect password."}
        if not user.is_active:
            return {"error": "Account deactivated. Contact administrator."}
        print(f"✅ User logged in: {email}")
        return {
            "api_key": user.key,
            "owner": user.owner_name,
            "email": user.email
        }
    finally:
        db.close()


def create_api_key(owner_name: str, key: str = None) -> str:
    """Legacy helper — kept for admin use."""
    db = SessionLocal()
    try:
        if not key:
            key = f"sk-{uuid.uuid4().hex[:32]}"
        api_key = APIKey(
            key=key,
            owner_name=owner_name,
            email=f"{owner_name.lower()}@admin.local",
            hashed_password=hash_password("admin123")
        )
        db.add(api_key)
        db.commit()
        print(f"✅ API key created for {owner_name}: {key}")
        return key
    finally:
        db.close()


def get_or_create_session(db, api_key_id: int, session_id: str = None):
    if session_id:
        session = db.query(Session).filter(Session.id == session_id).first()
        if session:
            session.last_active = datetime.utcnow()
            db.commit()
            return session

    session = Session(api_key_id=api_key_id)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def save_chat(db, session_id, question, answer, language, confidence, sources, suggestions):
    chat = ChatHistory(
        session_id=session_id,
        question=question,
        answer=answer,
        language=language,
        confidence=confidence,
        sources=str(sources),
        suggestions="|".join(suggestions)
    )
    db.add(chat)
    db.commit()
    db.refresh(chat)
    return chat


def save_document(db, session_id, filename, file_path):
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


def update_document_status(db, doc_id, status, summary=""):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if doc:
        doc.status = status
        doc.summary = summary
        db.commit()
    return doc