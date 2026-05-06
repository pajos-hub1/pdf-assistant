import os
import time
from fastapi import BackgroundTasks
from sqlalchemy.orm import Session
from app.database import (
    SessionLocal,
    update_document_status,
    Document
)
from app.ingestor import ingest_pdf
from app.chain import build_qa_chain, generate_summary
from app.logger import log_upload, log_error

# In-memory store for vector stores and chains per session
# This gets populated as background tasks complete
session_chains = {}
session_stores = {}


# ─────────────────────────────────────────
# BACKGROUND TASK
# ─────────────────────────────────────────

def process_pdf_background(
    doc_id: int,
    file_path: str,
    session_id: str,
    owner: str,
    filename: str
):
    """
    Runs in the background after upload.
    Handles OCR + ingestion + summary + chain building.
    User gets immediate response while this runs silently.
    """
    db = SessionLocal()
    start_time = time.time()

    try:
        print(f"⚙️  Background task started for {filename} (session: {session_id})")

        # Step 1: Get existing store for this session if any
        existing_store = session_stores.get(session_id, None)

        # Step 2: Run OCR + ingestion
        vector_store = ingest_pdf(file_path, existing_store=existing_store)

        # Step 3: Save store for this session
        session_stores[session_id] = vector_store

        # Step 4: Build RAG chain for this session
        chain, retriever = build_qa_chain(vector_store)
        session_chains[session_id] = {
            "chain": chain,
            "retriever": retriever
        }

        # Step 5: Generate document summary
        print(f"📝 Generating summary for {filename}...")
        docs = retriever.invoke("main topic summary overview")
        summary = generate_summary(docs)

        # Step 6: Update document status in DB → done
        update_document_status(
            db=db,
            doc_id=doc_id,
            status="done",
            summary=summary
        )

        # Step 7: Log success
        duration_ms = (time.time() - start_time) * 1000
        num_pages = len(docs)
        log_upload(
            session_id=session_id,
            owner=owner,
            filename=filename,
            num_pages=num_pages,
            status="done",
            duration_ms=duration_ms
        )

        print(f"✅ Background task complete for {filename} — {round(duration_ms)}ms")

    except Exception as e:
        # Update document status → failed
        update_document_status(
            db=db,
            doc_id=doc_id,
            status="failed",
            summary=""
        )

        # Log error
        log_error(
            session_id=session_id,
            owner=owner,
            endpoint="/upload",
            error=str(e)
        )
        print(f"❌ Background task failed for {filename}: {e}")

    finally:
        db.close()


# ─────────────────────────────────────────
# HELPERS USED BY MAIN.PY
# ─────────────────────────────────────────

def get_session_chain(session_id: str):
    """Get the RAG chain for a session if processing is done."""
    return session_chains.get(session_id, None)


def get_session_store(session_id: str):
    """Get the vector store for a session."""
    return session_stores.get(session_id, None)


def get_document_status(doc_id: int) -> dict:
    """Check the processing status of a document."""
    db = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if not doc:
            return {"status": "not_found"}
        return {
            "status": doc.status,
            "filename": doc.filename,
            "summary": doc.summary,
            "uploaded_at": doc.uploaded_at
        }
    finally:
        db.close()


def clear_session_data(session_id: str):
    """Clear in-memory chain and store for a session."""
    session_chains.pop(session_id, None)
    session_stores.pop(session_id, None)
    print(f"🗑️  Cleared in-memory data for session: {session_id}")