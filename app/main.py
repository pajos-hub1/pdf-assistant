from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import os

from app.database import init_db, SessionLocal, Document
from app.logger import log_startup
from app.routers import auth, chats, documents, qa, admin

# ─────────────────────────────────────────
# APP SETUP
# ─────────────────────────────────────────

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="PDF Document Assistant",
    description="A RAG-based PDF assistant — 100% free stack",
    version="3.0.0"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────
# ROUTERS
# ─────────────────────────────────────────

app.include_router(auth.router)
app.include_router(chats.router)
app.include_router(documents.router)
app.include_router(qa.router)
app.include_router(admin.router)


# ─────────────────────────────────────────
# PUBLIC
# ─────────────────────────────────────────

@app.get("/health", tags=["Public"])
async def health():
    return {
        "status": "ok",
        "model": "llama3.2",
        "cost": "$0.00",
        "version": "3.0.0"
    }


# ─────────────────────────────────────────
# STARTUP
# ─────────────────────────────────────────

@app.on_event("startup")
async def startup():
    init_db()
    log_startup()

    from app.tasks import session_chains, session_stores
    from app.chain import build_qa_chain
    from langchain_huggingface import HuggingFaceEmbeddings
    from langchain_community.vectorstores import FAISS

    db = SessionLocal()
    try:
        completed_docs = (
            db.query(Document)
            .filter(Document.status == "done")
            .all()
        )

        session_ids = list(set([doc.session_id for doc in completed_docs]))

        if session_ids:
            embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )
            for session_id in session_ids:
                faiss_path = f"data/{session_id}/faiss_index"
                if os.path.exists(faiss_path):
                    try:
                        vector_store = FAISS.load_local(
                            faiss_path,
                            embeddings,
                            allow_dangerous_deserialization=True
                        )
                        chain, retriever = build_qa_chain(vector_store)
                        session_stores[session_id] = vector_store
                        session_chains[session_id] = {
                            "chain": chain,
                            "retriever": retriever
                        }
                        print(f"✅ Reloaded session: {session_id}")
                    except Exception as e:
                        print(f"⚠️  Failed to reload session {session_id}: {e}")
    finally:
        db.close()

    print("✅ PDF Assistant is ready")