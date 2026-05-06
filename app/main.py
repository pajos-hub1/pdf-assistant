from fastapi import FastAPI, UploadFile, File, Depends, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette.requests import Request
import shutil
import os
import time

from app.database import (
    init_db,
    get_db,
    save_chat,
    save_document,
    update_document_status,
    create_api_key,
    ChatHistory,
    Document,
    Session as DBSession
)
from app.auth import validate_api_key, get_current_session, list_all_keys
from app.logger import log_query, log_error, log_startup, log_session_created
from app.tasks import (
    process_pdf_background,
    get_session_chain,
    get_session_store,
    get_document_status,
    clear_session_data
)
from app.chain import (
    generate_suggestions,
    detect_language,
    calculate_confidence
)
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from app.ingestor import FAISS_INDEX_PATH


# ─────────────────────────────────────────
# APP SETUP
# ─────────────────────────────────────────

# Rate limiter — 10 requests per minute per IP on /ask
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="PDF Document Assistant")

# Rate limit error handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS — needed for frontend later
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # restrict to your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────
# MODELS
# ─────────────────────────────────────────

class QuestionRequest(BaseModel):
    question: str
    session_id: str  # user passes their session_id

class RegisterRequest(BaseModel):
    owner_name: str


# ─────────────────────────────────────────
# STARTUP
# ─────────────────────────────────────────

@app.on_event("startup")
async def startup():
    """Initialize DB and log startup."""
    init_db()
    log_startup()
    print("✅ PDF Assistant is ready")


# ─────────────────────────────────────────
# PUBLIC ENDPOINTS — no auth required
# ─────────────────────────────────────────

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "model": "llama3.2",
        "cost": "$0.00"
    }


@app.post("/auth/register")
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """
    Public endpoint — register and get an API key.
    In production add email + password + bcrypt hashing here.
    """
    key = create_api_key(owner_name=request.owner_name)
    return {
        "message": "✅ Registration successful",
        "owner": request.owner_name,
        "api_key": key,
        "instructions": "Add this key to every request as X-API-Key header"
    }


# ─────────────────────────────────────────
# PROTECTED ENDPOINTS — auth required
# ─────────────────────────────────────────

@app.post("/upload")
async def upload_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    auth: dict = Depends(get_current_session)
):
    """Upload a PDF — processed in background, returns immediately."""
    session = auth["session"]
    owner = auth["owner"]

    file_path = f"data/{session.id}/{file.filename}"
    os.makedirs(f"data/{session.id}", exist_ok=True)

    # Save file to disk
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Save document record to DB with status=processing
    doc = save_document(
        db=db,
        session_id=session.id,
        filename=file.filename,
        file_path=file_path
    )

    # Log session created if first upload
    log_session_created(session_id=session.id, owner=owner)

    # Schedule background OCR + ingestion
    background_tasks.add_task(
        process_pdf_background,
        doc_id=doc.id,
        file_path=file_path,
        session_id=session.id,
        owner=owner,
        filename=file.filename
    )

    return {
        "message": f"✅ {file.filename} received — processing in background.",
        "doc_id": doc.id,
        "session_id": session.id,
        "status": "processing",
        "tip": f"Check status at GET /status/{doc.id}"
    }


@app.get("/status/{doc_id}")
async def check_status(
    doc_id: int,
    auth: dict = Depends(get_current_session)
):
    """Check if a document has finished processing."""
    status = get_document_status(doc_id)
    return status


@app.post("/ask")
@limiter.limit("10/minute")  # Rate limit — 10 questions per minute per IP
async def ask_question(
    request: Request,
    body: QuestionRequest,
    db: Session = Depends(get_db),
    auth: dict = Depends(get_current_session)
):
    session = auth["session"]
    owner = auth["owner"]
    start_time = time.time()

    # Get session chain — check if processing is done
    session_data = get_session_chain(session.id)

    if not session_data:
        raise HTTPException(
            status_code=400,
            detail="❌ No document ready yet. Upload a PDF and wait for processing to complete."
        )

    chain = session_data["chain"]
    retriever = session_data["retriever"]
    vector_store = get_session_store(session.id)

    try:
        # Feature 4: Detect language
        language = detect_language(body.question)

        # Feature 2: Get docs with confidence scores
        docs_with_scores = vector_store.similarity_search_with_score(
            body.question, k=5
        )
        docs = [doc for doc, score in docs_with_scores]
        scores = [score for doc, score in docs_with_scores]
        confidence = calculate_confidence(scores)

        # Get source pages
        sources = sorted(set([
            doc.metadata.get("page", "unknown") for doc in docs
        ]))

        # Invoke RAG chain with DB-backed memory
        answer = chain.invoke(
            {
                "question": body.question,
                "language": language
            },
            config={"configurable": {"session_id": session.id}}
        )

        # Feature 3: Generate suggestions
        suggestions = generate_suggestions(body.question, answer)

        # Save to DB — replaces chat_history = []
        save_chat(
            db=db,
            session_id=session.id,
            question=body.question,
            answer=answer,
            language=language,
            confidence=confidence,
            sources=sources,
            suggestions=suggestions
        )

        # Log query
        duration_ms = (time.time() - start_time) * 1000
        log_query(
            session_id=session.id,
            owner=owner,
            question=body.question,
            answer=answer,
            language=language,
            confidence=confidence,
            sources=sources,
            duration_ms=duration_ms
        )

        return {
            "answer": answer,
            "confidence": confidence,
            "sources": f"Pages: {sources}",
            "suggestions": suggestions,
            "language_detected": language,
            "session_id": session.id
        }

    except Exception as e:
        log_error(
            session_id=session.id,
            owner=owner,
            endpoint="/ask",
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=f"❌ Error: {str(e)}")


@app.get("/history")
async def get_history(
    db: Session = Depends(get_db),
    auth: dict = Depends(get_current_session)
):
    """Get chat history for current session from DB."""
    session = auth["session"]
    records = (
        db.query(ChatHistory)
        .filter(ChatHistory.session_id == session.id)
        .order_by(ChatHistory.created_at.asc())
        .all()
    )
    return {
        "session_id": session.id,
        "owner": auth["owner"],
        "history": [
            {
                "question": r.question,
                "answer": r.answer,
                "language": r.language,
                "confidence": r.confidence,
                "sources": r.sources,
                "suggestions": r.suggestions.split("|") if r.suggestions else [],
                "created_at": r.created_at
            }
            for r in records
        ]
    }


@app.get("/documents")
async def get_documents(
    db: Session = Depends(get_db),
    auth: dict = Depends(get_current_session)
):
    """Get all uploaded documents for current session."""
    session = auth["session"]
    docs = (
        db.query(Document)
        .filter(Document.session_id == session.id)
        .all()
    )
    return {
        "session_id": session.id,
        "documents": [
            {
                "id": d.id,
                "filename": d.filename,
                "status": d.status,
                "summary": d.summary,
                "uploaded_at": d.uploaded_at
            }
            for d in docs
        ]
    }


@app.delete("/history")
async def clear_history(
    db: Session = Depends(get_db),
    auth: dict = Depends(get_current_session)
):
    """Clear chat history for current session from DB."""
    session = auth["session"]
    db.query(ChatHistory).filter(
        ChatHistory.session_id == session.id
    ).delete()
    db.commit()
    return {"message": "✅ Chat history cleared."}


@app.delete("/documents")
async def clear_documents(
    db: Session = Depends(get_db),
    auth: dict = Depends(get_current_session)
):
    """Clear all documents and data for current session."""
    session = auth["session"]

    # Clear DB records
    db.query(ChatHistory).filter(
        ChatHistory.session_id == session.id
    ).delete()
    db.query(Document).filter(
        Document.session_id == session.id
    ).delete()
    db.commit()

    # Clear in-memory chains
    clear_session_data(session.id)

    # Clear FAISS index for session
    session_faiss_path = f"data/{session.id}/faiss_index"
    if os.path.exists(session_faiss_path):
        shutil.rmtree(session_faiss_path)

    return {"message": "✅ All documents and history cleared."}


# ─────────────────────────────────────────
# ADMIN ENDPOINTS
# ─────────────────────────────────────────

@app.get("/admin/keys")
async def admin_list_keys(
    db: Session = Depends(get_db),
    auth: dict = Depends(get_current_session)
):
    """List all API keys — admin use only."""
    return {"keys": list_all_keys(db)}