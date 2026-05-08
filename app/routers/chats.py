from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import (
    get_db, get_all_chats, create_new_chat,
    rename_chat, delete_chat,
    ChatHistory, Document
)
from app.database import Session as DBSession
from app.auth import validate_api_key, get_current_session
from app.tasks import clear_session_data
from app.services.export import export_as_txt, export_as_pdf
import shutil
import os

router = APIRouter(prefix="/chats", tags=["Chats"])


class NewChatRequest(BaseModel):
    name: str = "New Chat"


class RenameChatRequest(BaseModel):
    name: str


@router.get("")
async def get_chats(
    db: Session = Depends(get_db),
    auth=Depends(validate_api_key)
):
    chats = get_all_chats(db, api_key_id=auth.id)
    return {"chats": chats}


@router.post("/new")
async def new_chat(
    body: NewChatRequest,
    db: Session = Depends(get_db),
    auth=Depends(validate_api_key)
):
    session = create_new_chat(db, api_key_id=auth.id, name=body.name)
    return {
        "message": "✅ New chat created",
        "session_id": session.id,
        "name": session.name,
        "created_at": session.created_at
    }


@router.patch("/{session_id}/rename")
async def rename_chat_endpoint(
    session_id: str,
    body: RenameChatRequest,
    db: Session = Depends(get_db),
    auth=Depends(validate_api_key)
):
    session = rename_chat(db, session_id=session_id, name=body.name)
    if not session:
        raise HTTPException(status_code=404, detail="Chat not found.")
    return {
        "message": "✅ Chat renamed",
        "session_id": session.id,
        "name": session.name
    }


@router.delete("/{session_id}")
async def delete_chat_endpoint(
    session_id: str,
    db: Session = Depends(get_db),
    auth=Depends(validate_api_key)
):
    clear_session_data(session_id)

    faiss_path = f"data/{session_id}/faiss_index"
    if os.path.exists(faiss_path):
        shutil.rmtree(faiss_path)

    success = delete_chat(db, session_id=session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Chat not found.")
    return {"message": "✅ Chat deleted successfully."}


@router.get("/{session_id}/history")
async def get_chat_history(
    session_id: str,
    db: Session = Depends(get_db),
    auth=Depends(validate_api_key)
):
    records = (
        db.query(ChatHistory)
        .filter(ChatHistory.session_id == session_id)
        .order_by(ChatHistory.created_at.asc())
        .all()
    )
    return {
        "session_id": session_id,
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


@router.get("/{session_id}/documents")
async def get_chat_documents(
    session_id: str,
    db: Session = Depends(get_db),
    auth=Depends(validate_api_key)
):
    docs = (
        db.query(Document)
        .filter(Document.session_id == session_id)
        .all()
    )
    return {
        "session_id": session_id,
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


@router.get("/{session_id}/export")
async def export_chat(
    session_id: str,
    format: str = "txt",
    db: Session = Depends(get_db),
    auth=Depends(validate_api_key)
):
    session = db.query(DBSession).filter(DBSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat not found.")

    records = (
        db.query(ChatHistory)
        .filter(ChatHistory.session_id == session_id)
        .order_by(ChatHistory.created_at.asc())
        .all()
    )

    docs = (
        db.query(Document)
        .filter(Document.session_id == session_id)
        .all()
    )

    chat_name = session.name or "Chat Export"
    doc_names = [d.filename for d in docs]

    if format == "pdf":
        return export_as_pdf(chat_name, records, doc_names, session_id)
    return export_as_txt(chat_name, records, doc_names, session_id)