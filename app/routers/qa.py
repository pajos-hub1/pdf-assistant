from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.database import get_db, save_chat, ChatHistory
from app.database import ChatHistory as ChatHistoryModel
from app.auth import get_current_session
from app.tasks import get_session_chain, get_session_store
from app.chain import (
    detect_language, calculate_confidence,
    generate_suggestions, ollama_stream,
    get_session_history
)
from app.logger import log_query, log_error
from langchain_core.messages import HumanMessage, AIMessage
import time
import json

router = APIRouter(tags=["QA"])
limiter = Limiter(key_func=get_remote_address)


class QuestionRequest(BaseModel):
    question: str


@router.get("/history")
async def get_history(
    db: Session = Depends(get_db),
    auth: dict = Depends(get_current_session)
):
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


@router.delete("/history")
async def clear_history(
    db: Session = Depends(get_db),
    auth: dict = Depends(get_current_session)
):
    session = auth["session"]
    db.query(ChatHistory).filter(
        ChatHistory.session_id == session.id
    ).delete()
    db.commit()
    return {"message": "✅ Chat history cleared for this session."}


@router.post("/ask/stream")
async def ask_stream(
    request: Request,
    body: QuestionRequest,
    db: Session = Depends(get_db),
    auth: dict = Depends(get_current_session)
):
    session = auth["session"]
    owner = auth["owner"]
    start_time = time.time()

    session_data = get_session_chain(session.id)
    if not session_data:
        raise HTTPException(
            status_code=400,
            detail="❌ No document ready yet."
        )

    vector_store = get_session_store(session.id)

    language = detect_language(body.question)
    if not language or language.lower() == "none":
        language = "English"

    docs_with_scores = vector_store.similarity_search_with_score(
        body.question, k=5
    )
    docs = [doc for doc, score in docs_with_scores]
    scores = [score for doc, score in docs_with_scores]
    confidence = calculate_confidence(scores)
    sources = sorted(set([
        doc.metadata.get("page", "unknown") for doc in docs
    ]))
    context = "\n\n".join([doc.page_content for doc in docs])

    records = (
        db.query(ChatHistoryModel)
        .filter(ChatHistoryModel.session_id == session.id)
        .order_by(ChatHistoryModel.created_at.asc())
        .all()
    )
    history = []
    for record in records:
        history.append(HumanMessage(content=record.question))
        history.append(AIMessage(content=record.answer))

    state = {"full_answer": [], "suggestions": []}

    def generate():
        try:
            for token in ollama_stream(body.question, context, history):
                state["full_answer"].append(token)
                yield f"data: {json.dumps({'token': token})}\n\n"

            complete_answer = "".join(state["full_answer"])

            save_chat(
                db=db,
                session_id=session.id,
                question=body.question,
                answer=complete_answer,
                language=language,
                confidence=confidence,
                sources=sources,
                suggestions=[]
            )

            duration_ms = (time.time() - start_time) * 1000
            log_query(
                session_id=session.id,
                owner=owner,
                question=body.question,
                answer=complete_answer,
                language=language,
                confidence=confidence,
                sources=sources,
                duration_ms=duration_ms
            )

            yield f"data: {json.dumps({'done': True, 'confidence': confidence, 'sources': sources, 'suggestions': [], 'language': language})}\n\n"

            suggestions = generate_suggestions(body.question, complete_answer)
            if suggestions:
                yield f"data: {json.dumps({'suggestions': suggestions})}\n\n"

        except Exception as e:
            print(f"❌ Stream error: {str(e)}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Transfer-Encoding": "chunked"
        }
    )