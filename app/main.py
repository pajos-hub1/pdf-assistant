from fastapi import FastAPI, UploadFile, File, Depends, BackgroundTasks, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette.requests import Request
from typing import Optional
import shutil
import os
import time

from app.database import (
    init_db,
    get_db,
    save_chat,
    save_document,
    create_api_key,
    ChatHistory,
    Document,
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


# ─────────────────────────────────────────
# APP SETUP
# ─────────────────────────────────────────

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="PDF Document Assistant",
    description="A RAG-based PDF assistant — 100% free stack",
    version="2.0.0"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # restrict to frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────
# REQUEST MODELS
# ─────────────────────────────────────────

class QuestionRequest(BaseModel):
    question: str  # session_id now comes from X-Session-Id header

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

@app.get("/health", tags=["Public"])
async def health():
    """Check if server is running."""
    return {
        "status": "ok",
        "model": "llama3.2",
        "cost": "$0.00",
        "version": "2.0.0"
    }


@app.post("/auth/register", tags=["Public"])
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """
    Register and get an API key.
    Pass this key as X-API-Key header in all future requests.
    """
    key = create_api_key(owner_name=request.owner_name)
    return {
        "message": "✅ Registration successful",
        "owner": request.owner_name,
        "api_key": key,
        "instructions": {
            "step1": "Copy your api_key above",
            "step2": "Click Authorize at the top of Swagger UI",
            "step3": "Paste your key and click Authorize",
            "step4": "All protected endpoints now work automatically"
        }
    }


# ─────────────────────────────────────────
# PROTECTED ENDPOINTS — auth required
# ─────────────────────────────────────────

@app.post("/upload", tags=["Documents"])
async def upload_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    auth: dict = Depends(get_current_session)
):
    """
    Upload a PDF — processed in background.
    Returns immediately with doc_id and session_id.
    Use GET /status/{doc_id} to check when processing is complete.

    Headers required:
    - X-API-Key: your api key
    - X-Session-Id: your session id (optional on first request)
    """
    session = auth["session"]
    owner = auth["owner"]

    # Create per-session data directory
    session_dir = f"data/{session.id}"
    os.makedirs(session_dir, exist_ok=True)
    file_path = f"{session_dir}/{file.filename}"

    # Save file to disk
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Save document record to DB — status: processing
    doc = save_document(
        db=db,
        session_id=session.id,
        filename=file.filename,
        file_path=file_path
    )

    # Log session
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
        "next_step": f"Check processing status at GET /status/{doc.id}",
        "tip": "Save your session_id and pass it as X-Session-Id header in all future requests"
    }


@app.get("/status/{doc_id}", tags=["Documents"])
async def check_status(
    doc_id: int,
    auth: dict = Depends(get_current_session)
):
    """
    Check if a document has finished processing.
    Status will be: processing | done | failed

    Headers required:
    - X-API-Key: your api key
    - X-Session-Id: your session id
    """
    status = get_document_status(doc_id)
    return status


@app.get("/documents", tags=["Documents"])
async def get_documents(
    db: Session = Depends(get_db),
    auth: dict = Depends(get_current_session)
):
    """
    Get all uploaded documents for current session.

    Headers required:
    - X-API-Key: your api key
    - X-Session-Id: your session id
    """
    session = auth["session"]
    docs = (
        db.query(Document)
        .filter(Document.session_id == session.id)
        .all()
    )
    return {
        "session_id": session.id,
        "owner": auth["owner"],
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


@app.delete("/documents", tags=["Documents"])
async def clear_documents(
    db: Session = Depends(get_db),
    auth: dict = Depends(get_current_session)
):
    """
    Clear all documents and chat history for current session.

    Headers required:
    - X-API-Key: your api key
    - X-Session-Id: your session id
    """
    session = auth["session"]

    # Clear DB records
    db.query(ChatHistory).filter(
        ChatHistory.session_id == session.id
    ).delete()
    db.query(Document).filter(
        Document.session_id == session.id
    ).delete()
    db.commit()

    # Clear in-memory chains and stores
    clear_session_data(session.id)

    # Remove FAISS index from disk
    session_faiss_path = f"data/{session.id}/faiss_index"
    if os.path.exists(session_faiss_path):
        shutil.rmtree(session_faiss_path)

    return {"message": "✅ All documents and history cleared for this session."}


@app.post("/ask", tags=["QA"])
@limiter.limit("10/minute")
async def ask_question(
    request: Request,
    body: QuestionRequest,
    db: Session = Depends(get_db),
    auth: dict = Depends(get_current_session)
):
    """
    Ask a question about your uploaded document.
    Rate limited to 10 requests per minute.

    Headers required:
    - X-API-Key: your api key
    - X-Session-Id: your session id
    """
    session = auth["session"]
    owner = auth["owner"]
    start_time = time.time()

    # Check if document processing is complete
    session_data = get_session_chain(session.id)
    if not session_data:
        raise HTTPException(
            status_code=400,
            detail=(
                "❌ No document ready yet. "
                "Upload a PDF and wait for status to be 'done' "
                "before asking questions."
            )
        )

    chain = session_data["chain"]
    vector_store = get_session_store(session.id)

    try:
        # Feature 4: Detect language of question
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

        # Invoke RAG chain with DB-backed memory per session
        answer = chain.invoke(
            {
                "question": body.question,
                "language": language
            },
            config={"configurable": {"session_id": session.id}}
        )

        # Feature 3: Generate follow-up suggestions
        suggestions = generate_suggestions(body.question, answer)

        # Save Q&A to DB — replaces chat_history = []
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

        # Log query to analytics.log
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
            "session_id": session.id,
            "response_time_ms": round(duration_ms, 2)
        }

    except Exception as e:
        log_error(
            session_id=session.id,
            owner=owner,
            endpoint="/ask",
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"❌ Error processing question: {str(e)}"
        )


@app.get("/history", tags=["QA"])
async def get_history(
    db: Session = Depends(get_db),
    auth: dict = Depends(get_current_session)
):
    """
    Get full chat history for current session from DB.

    Headers required:
    - X-API-Key: your api key
    - X-Session-Id: your session id
    """
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
        "total": len(records),
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


@app.delete("/history", tags=["QA"])
async def clear_history(
    db: Session = Depends(get_db),
    auth: dict = Depends(get_current_session)
):
    """
    Clear chat history for current session from DB.

    Headers required:
    - X-API-Key: your api key
    - X-Session-Id: your session id
    """
    session = auth["session"]
    db.query(ChatHistory).filter(
        ChatHistory.session_id == session.id
    ).delete()
    db.commit()
    return {"message": "✅ Chat history cleared for this session."}


# ─────────────────────────────────────────
# ADMIN ENDPOINTS
# ─────────────────────────────────────────

@app.get("/admin/keys", tags=["Admin"])
async def admin_list_keys(
    db: Session = Depends(get_db),
    auth: dict = Depends(get_current_session)
):
    """List all API keys — admin use only."""
    return {"keys": list_all_keys(db)}