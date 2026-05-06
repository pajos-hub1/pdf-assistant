import os
import time
from sqlalchemy.orm import Session
from app.database import (
    SessionLocal,
    update_document_status,
    Document
)
from app.ingestor import ingest_pdf
from app.chain import build_qa_chain, generate_summary
from app.logger import log_upload, log_error

# Module-level stores — shared across all requests
session_chains = {}
session_stores = {}


def process_pdf_background(
    doc_id: int,
    file_path: str,
    session_id: str,
    owner: str,
    filename: str
):
    db = SessionLocal()
    start_time = time.time()

    try:
        print(f"⚙️  Background task started for {filename} (session: {session_id})")

        existing_store = session_stores.get(session_id, None)
        vector_store = ingest_pdf(file_path, existing_store=existing_store)
        session_stores[session_id] = vector_store

        chain, retriever = build_qa_chain(vector_store)
        session_chains[session_id] = {
            "chain": chain,
            "retriever": retriever
        }

        print(f"📝 Generating summary for {filename}...")
        docs = retriever.invoke("main topic summary overview")
        summary = generate_summary(docs)

        # Save FAISS index to disk
        faiss_path = f"data/{session_id}/faiss_index"
        os.makedirs(faiss_path, exist_ok=True)
        vector_store.save_local(faiss_path)
        print(f"💾 FAISS index saved to {faiss_path}")

        update_document_status(
            db=db,
            doc_id=doc_id,
            status="done",
            summary=summary
        )

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
        update_document_status(db=db, doc_id=doc_id, status="failed", summary="")
        log_error(session_id=session_id, owner=owner, endpoint="/upload", error=str(e))
        print(f"❌ Background task failed for {filename}: {e}")

    finally:
        db.close()


def get_session_chain(session_id: str):
    return session_chains.get(session_id, None)


def get_session_store(session_id: str):
    return session_stores.get(session_id, None)


def get_document_status(doc_id: int) -> dict:
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
    session_chains.pop(session_id, None)
    session_stores.pop(session_id, None)
    print(f"🗑️  Cleared in-memory data for session: {session_id}")