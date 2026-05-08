from fastapi import APIRouter, UploadFile, File, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from app.database import get_db, save_document, Document, ChatHistory
from app.auth import get_current_session
from app.tasks import (
    process_pdf_background, get_document_status,
    session_chains, session_stores
)
from app.logger import log_session_created
from app.chain import build_qa_chain
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
import shutil
import os

router = APIRouter(tags=["Documents"])


@router.post("/upload")
async def upload_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    auth: dict = Depends(get_current_session)
):
    session = auth["session"]
    owner = auth["owner"]

    session_dir = f"data/{session.id}"
    os.makedirs(session_dir, exist_ok=True)
    file_path = f"{session_dir}/{file.filename}"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    doc = save_document(
        db=db,
        session_id=session.id,
        filename=file.filename,
        file_path=file_path
    )

    log_session_created(session_id=session.id, owner=owner)

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


@router.get("/status/{doc_id}")
async def check_status(
    doc_id: int,
    auth: dict = Depends(get_current_session)
):
    return get_document_status(doc_id)


@router.get("/documents")
async def get_documents(
    db: Session = Depends(get_db),
    auth: dict = Depends(get_current_session)
):
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


@router.delete("/documents")
async def clear_documents(
    db: Session = Depends(get_db),
    auth: dict = Depends(get_current_session)
):
    session = auth["session"]

    db.query(ChatHistory).filter(
        ChatHistory.session_id == session.id
    ).delete()
    db.query(Document).filter(
        Document.session_id == session.id
    ).delete()
    db.commit()

    session_chains.pop(session.id, None)
    session_stores.pop(session.id, None)

    faiss_path = f"data/{session.id}/faiss_index"
    if os.path.exists(faiss_path):
        shutil.rmtree(faiss_path)

    return {"message": "✅ All documents and history cleared for this session."}